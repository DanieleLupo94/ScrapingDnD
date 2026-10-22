"""
Converte i file HTML estratti in JSON strutturato.
Gestisce 6 strutture HTML diverse presenti nel compendium D&D 4e.

Uso:
    python parse_html.py [--input DIR] [--output DIR] [--category CAT] [--multithread]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------

SOURCE_RE = re.compile(r"Published in (.+?)(?:,\s*page\(s\)\s*(.+?))?\.?\s*$")
LEVEL_RE = re.compile(r"^(.*?)\s+(Attack|Utility|Feature|Channel Divinity|Prayer)\s+(\d+)?$")

POWER_H1_CLASSES = {"encounterpower", "dailypower", "atwillpower"}

POWER_KNOWN_LABELS = {
    "Target", "Targets", "Attack", "Hit", "Miss", "Effect", "Trigger",
    "Requirement", "Special", "Note",
    "Primary Attack", "Secondary Attack", "Tertiary Attack",
    "Primary Target", "Secondary Target", "Tertiary Target", "Secondary Targets",
    "Hit (AC)", "Hit (Fortitude)", "Hit (Reflex)", "Hit (Will)",
    "Sustain Minor", "Sustain Standard", "Sustain Move", "Sustain Free", "Sustain No Action",
    "Aftereffect", "Aftereffect (Slowed)",
    "First Failed Saving Throw", "Second Failed Saving Throw",
    "Third Failed Saving Throw", "Each Failed Saving Throw",
    "Each Additional Failed Saving Throw",
    "Prerequisite", "Channel Divinity", "Keyword", "Keywords",
    "Secondary Attack Keywords", "Range",
    "Opportunity Attack", "Opportunity Action", "Immediate Interrupt",
    "Level 13", "Level 15", "Level 17", "Level 19", "Level 21",
    "Level 23", "Level 25", "Level 27", "Level 29",
    "Level 13 Swap", "Level 15 Swap", "Level 17 Swap", "Level 19 Swap",
    "Level 21 Swap", "Level 23 Swap", "Level 25 Swap", "Level 27 Swap", "Level 29 Swap",
    "Level 13 Swap: Hit", "Level 19 Swap: Hit", "Level 23 Swap: Hit",
    "Level 29 Swap: Hit", "Level 19 Swap: Effect", "Level 29 Swap: Effect",
    "At-Will", "At-will", "At-Will (Special)", "Encounter", "Daily",
    "Standard Action", "Minor Action", "Move Action", "Free Action",
    "No Action", "Opportunity Action",
    "Rageblood Vigor", "Thaneborn Triumph", "Thunderborn Wrath",
    "Whirling Slayer", "Berserker Fury",
    "Primal Guardian", "Primal Predator", "Primal Swarm",
    "Censure of Pursuit", "Censure of Retribution", "Censure of Unity",
    "Night Stalker", "Bleak Disciple",
    "Virtue of Cunning", "Virtue of Valor", "Virtue of Prescience",
    "Infernal Pact", "Vestige Pact",
    "Ascendant Commander Pact Boon", "Eyes of the Vestige Augment",
    "Brawler Style", "Instinctive Effect",
    "Divine Favor", "Healing Favor (Healing)", "Martial Favor",
    "Rune of Destruction", "Rune of Protection",
    "Close",
    "1. Air", "2. Earth", "3. Fire", "4. Water",
    "Weapon", "Axe", "Mace", "Heavy Blade", "Spear or Polearm",
    "Phase of the Sun", "Phase of the Moon", "Phase of the Stars",
    "Blazing Sun", "Watching Moon", "Distant Stars",
    "Mantle of Clarity", "Mantle of Elation", "Mantle of Impulsiveness",
    "Aegis of Assault",
    "Covenant of Preservation", "Covenant of Wrath",
    "Covenant of Malediction", "Covenant of Malediction (Fear)",
    "Karmath pact Boon", "Sea Tyrant Pact Boon", "Kulnoghrim Pact Boon",
    "Lawbreaker", "Lawbreaker's Doom",
    "1 target", "2 targets", "3, 4, or 5 targets",
    "Secondary Damage",
    # Familiar/spirit subtype labels
    "Beast", "Active Familiar",
    "Stalker Spirit", "Protector Spirit", "World Speaker Spirit",
    "Watcher Spirit", "Elemental Spirit",
    # Rogue tactics
    "Artful Dodger", "Brutal Scoundrel", "Ruthless Ruffian",
    "Cunning Sneak", "Bloodbond", "Spiritbond", "Lawbreaker",
    "Brutal Scoundrel or Ruthless Ruffian",
    # Sorcerer wild/cosmic/storm/dragon magic
    "Wild Magic", "Chaos Sorcerer", "Cosmic Sorcerer", "Cosmic Magic",
    "Storm Magic", "Dragon Magic",
    # Hunter
    "Hunter Fighting Style",
    # Attack/Hit/Effect variant labels
    "Attack (Fortitude)", "Attack (Reflex)", "Attack (Will)", "Attack (Any)",
    "Hit (Any)", "Hit (Cold)", "Hit (Radiant)",
    "Effect (Cold)", "Effect (Radiant)", "Effect (Thunder)",
    "Power (Encounter)",
    # Range labels used as headings
    "Melee", "Area", "Close",
    # Level 11 swap
    "Level 11",
    # Generic
    "Property",
    # Swordmage aegis variants
    "Aegis of Ensnarement", "Aegis of Shielding",
    # Monk iron soul
    "Iron Soul",
    # Shaman spirit aspects
    "Aspect of the Ancients", "Aspect of the Destroyer", "Aspect of the Hunter",
    # Warden guardian forms
    "Earthstrength", "Wildblood", "Lifespirit", "Stormheart",
    # Damage type labels used as headings
    "Cold", "Radiant", "Fire", "Lightning", "Thunder",
    # Pact variants
    "Star Pact (Binder)",
    # Numbered sub-attacks / options
    "1.", "2.", "3.", "4.", "1-3", "4-6",
    # Familiar sub-commands (varie spaziature)
    "✦    Fetch", "✦    Carry", "✦    Manipulate",
    "✦ Fetch", "✦ Carry", "✦ Manipulate",
    # Aegis typo variant
    "Aegis of Ensarement",
    # Misc
    "Secondary Hit",
    "Standard Action (1/encounter)",
    "Move Action (Teleportation)",
    "Close burst 1",
    "Other",
    "*",
}

POWER_TYPE_MAP = {
    "atwillpower":    "at-will",
    "encounterpower": "encounter",
    "dailypower":     "daily",
}


# ---------------------------------------------------------------------------
# Utilità condivise
# ---------------------------------------------------------------------------

def extract_source(root: Tag) -> dict:
    p = root.find("p", class_="publishedIn")
    if not p:
        return {}
    a = p.find("a")
    if a:
        a.extract()
    raw = p.get_text(" ", strip=True)
    m = SOURCE_RE.match(raw)
    if m:
        r: dict = {"source": m.group(1).strip()}
        if m.group(2):
            r["source_pages"] = m.group(2).strip()
        return r
    return {"source": raw}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def set_or_append(record: dict, key: str, value: str) -> None:
    """Aggiunge il valore; se la chiave esiste già la converte in lista."""
    if key not in record:
        record[key] = value
    else:
        existing = record[key]
        if not isinstance(existing, list):
            record[key] = [existing]
        record[key].append(value)


# ---------------------------------------------------------------------------
# Parser 1 – Power (encounterpower / dailypower / atwillpower)
# ---------------------------------------------------------------------------

def _parse_level_line(text: str) -> dict:
    text = text.strip()
    m = LEVEL_RE.match(text)
    if m:
        lv = m.group(3)
        return {
            "class_name": m.group(1).strip(),
            "power_category": m.group(2),
            "level": int(lv) if lv else None,
        }
    return {"level_line": text}


def _parse_first_powerstat(tag: Tag) -> dict:
    result: dict = {}
    raw = str(tag).replace("&nbsp;", " ")
    soup = BeautifulSoup(raw, "html.parser")
    p = soup.find("p") or soup

    parts: list[str] = []
    buf: list[str] = []
    for child in p.children:
        if getattr(child, "name", None) == "br":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(child.get_text(" ") if hasattr(child, "get_text") else str(child))
    if buf:
        parts.append("".join(buf))

    if parts:
        line0 = clean(parts[0])
        if "✦" in line0:
            before, after = line0.split("✦", 1)
            result["usage"] = before.strip()
            result["keywords"] = [k.strip() for k in after.split(",") if k.strip()]
        else:
            result["usage"] = line0

    if len(parts) > 1:
        line1 = parts[1]
        m = re.split(r" {2,}", line1, maxsplit=1)
        if len(m) == 2:
            result["action_type"] = clean(m[0])
            result["range"] = clean(m[1])
        else:
            result["action_type"] = clean(line1)

    return result


def _label_and_text(p: Tag) -> tuple[str, str] | None:
    b = p.find("b")
    if not b:
        return None
    label = b.get_text(strip=True).rstrip(":").replace(" ", " ")
    label = re.sub(r"\s+", " ", label).strip()
    b.extract()
    text = clean(p.get_text(" "))
    text = text.lstrip(": ")
    return label, text


def parse_power(root: Tag) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    record: dict = {}

    h1_tags = root.find_all("h1")
    main_h1 = h1_tags[0]
    h1_class = (main_h1.get("class") or [""])[0]
    record["power_type"] = POWER_TYPE_MAP.get(h1_class, h1_class or "unknown")

    span_level = main_h1.find("span", class_="level")
    if span_level:
        record.update(_parse_level_line(span_level.get_text(strip=True)))
        span_level.extract()

    record["name"] = main_h1.get_text(strip=True)
    if len(h1_tags) > 1:
        record["sub_power_names"] = [h.get_text(strip=True) for h in h1_tags[1:]]

    first_stat_done = False
    for p in root.find_all("p"):
        cls = (p.get("class") or [""])[0]

        if cls == "publishedIn":
            continue

        if cls == "powerstat":
            if not first_stat_done:
                record.update(_parse_first_powerstat(p))
                first_stat_done = True
                continue
            parsed = _label_and_text(p)
            if parsed:
                label, text = parsed
                label = label.lstrip()
                if label not in POWER_KNOWN_LABELS:
                    warnings.append(f"Label non mappata (powerstat): '{label}'")
                set_or_append(record, label.lower().replace(" ", "_"), text)
            else:
                text = clean(p.get_text(" "))
                if text:
                    warnings.append(f"p.powerstat senza label: '{text[:60]}'")
            continue

        if cls == "flavor":
            i_tag = p.find("i")
            if i_tag and not p.find("b"):
                record.setdefault("flavor_text", i_tag.get_text(strip=True))
                continue
            parsed = _label_and_text(p)
            if parsed:
                label, text = parsed
                label = label.lstrip()
                if label not in POWER_KNOWN_LABELS:
                    warnings.append(f"Label non mappata (flavor): '{label}'")
                set_or_append(record, label.lower().replace(" ", "_"), text)

    record.update(extract_source(root))
    return record, warnings


# ---------------------------------------------------------------------------
# Parser 2 – Feat / Deity / Background (p.flavor con label separate da <br>)
# ---------------------------------------------------------------------------

def _parse_br_labels(tag: Tag) -> dict:
    """Parsa un tag con label <b>Label</b>: testo separate da <br>."""
    result: dict = {}
    current_label: str | None = None
    current_parts: list[str] = []

    def flush():
        if current_label:
            val = clean(" ".join(current_parts))
            if val:
                set_or_append(result, current_label, val)

    for child in tag.children:
        name = getattr(child, "name", None)
        if name == "br":
            flush()
            current_label = None
            current_parts = []
        elif name == "b":
            flush()
            current_label = child.get_text(strip=True).rstrip(": ").lower().replace(" ", "_")
            current_parts = []
        elif name == "i":
            current_parts.append(child.get_text(strip=True))
        elif isinstance(child, NavigableString):
            text = str(child).lstrip(": ").strip()
            if text:
                current_parts.append(text)
        elif name:
            current_parts.append(child.get_text(" ", strip=True))
    flush()
    return result


def parse_br_labeled(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1")
    record["name"] = h1.get_text(strip=True) if h1 else root.get("id", "")

    # p.flavor o p.flavortext con label separate da <br>
    for cls in ("flavor", "flavortext"):
        p = root.find("p", class_=cls)
        if p:
            record.update(_parse_br_labels(p))
            break

    # Testo libero fuori dai tag p (Background)
    raw_text_parts: list[str] = []
    for child in root.children:
        if getattr(child, "name", None) in (None, "br") and isinstance(child, NavigableString):
            t = child.strip()
            if t:
                raw_text_parts.append(t)
    if raw_text_parts:
        record.setdefault("description", clean(" ".join(raw_text_parts)))

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Parser 2b – Armor (label <b> e <br> diretti nel div.detail)
# ---------------------------------------------------------------------------

def parse_root_br_labeled(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1")
    record["name"] = h1.get_text(strip=True) if h1 else root.get("id", "")

    current_label: str | None = None
    current_parts: list[str] = []

    def flush():
        if current_label:
            val = clean(" ".join(current_parts))
            if val:
                set_or_append(record, current_label, val)

    for child in root.children:
        name = getattr(child, "name", None)
        if name == "h1":
            continue  # già estratto
        if name == "p":
            cls = child.get("class") or []
            if "publishedIn" in cls:
                continue
            # p generico → parte del testo corrente
            current_parts.append(child.get_text(" ", strip=True))
        elif name == "br":
            flush()
            current_label = None
            current_parts = []
        elif name == "b":
            flush()
            current_label = clean(child.get_text()).rstrip(": ").lower().replace(" ", "_")
            current_parts = []
        elif isinstance(child, NavigableString):
            text = str(child).lstrip(": ").strip()
            if text:
                current_parts.append(text)
        elif name:
            current_parts.append(child.get_text(" ", strip=True))
    flush()

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Parser 3 – Monster / Companion (h1.monster)
# ---------------------------------------------------------------------------

def parse_monster(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1", class_="monster")

    span_type = h1.find("span", class_="type") if h1 else None
    if span_type:
        record["creature_type"] = span_type.get_text(strip=True)
        span_type.extract()

    span_level = h1.find("span", class_="level") if h1 else None
    if span_level:
        span_xp = span_level.find("span", class_="xp")
        if span_xp:
            record["xp"] = clean(span_xp.get_text()).replace("XP", "").strip()
            span_xp.extract()
        record["level"] = clean(span_level.get_text())
        span_level.extract()

    if h1:
        record["name"] = clean(h1.get_text())

    # Stat block – primo p.flavor: bold label inline separati da <br>
    flavors = root.find_all("p", class_="flavor")
    for i, p in enumerate(flavors):
        cls2 = p.get("class", [])
        if "alt" not in cls2:
            if i == 0:
                record["stat_block"] = _parse_br_labels(p)
            break

    # Attacchi – p.flavor.alt + p.flavorIndent
    attacks: list[dict] = []
    current_attack: dict | None = None
    for p in root.find_all("p"):
        cls = p.get("class", [])
        if "flavor" in cls and "alt" in cls:
            if current_attack:
                attacks.append(current_attack)
            current_attack = {"header": clean(p.get_text(" "))}
        elif "flavorIndent" in cls:
            if current_attack is not None:
                current_attack.setdefault("details", []).append(clean(p.get_text(" ")))
    if current_attack:
        attacks.append(current_attack)
    if attacks:
        record["attacks"] = attacks

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Parser 4 – Magic Item / Weapon / Implement / Poison (h1.mihead / h1.poison)
# ---------------------------------------------------------------------------

def parse_magic_item(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1")

    span_level = h1.find("span") if h1 else None
    if span_level:
        record["item_level"] = clean(span_level.get_text())
        span_level.extract()
    if h1:
        record["name"] = clean(h1.get_text())

    # Descrizione flavor
    miflavor = root.find("p", class_="miflavor")
    if miflavor:
        record["description"] = clean(miflavor.get_text())

    # Tabella tier (es. Weapon +4/+5/+6)
    table = root.find("table", class_="magicitem")
    if table:
        tiers: list[dict] = []
        for row in table.find_all("tr"):
            cells = [clean(td.get_text()) for td in row.find_all("td") if clean(td.get_text())]
            if cells:
                tiers.append(cells)
        record["tiers"] = tiers

    # Proprietà e poteri
    properties: list[str] = []
    powers: list[dict] = []
    current_power: dict | None = None

    for tag in root.children:
        name = getattr(tag, "name", None)
        if name == "h2":
            if current_power:
                powers.append(current_power)
            current_power = {"header": clean(tag.get_text())}
        elif name == "p":
            cls = tag.get("class") or []
            if "mistat" in cls:
                text = clean(tag.get_text(" "))
                if "indent" in cls:
                    if current_power is not None:
                        current_power.setdefault("text", []).append(text)
                    else:
                        properties.append(text)
                else:
                    if current_power is not None:
                        current_power.setdefault("properties", []).append(text)
                    else:
                        properties.append(text)
            elif "mitext" in cls:
                record.setdefault("lore", []).append(clean(tag.get_text(" ")))

    if current_power:
        powers.append(current_power)

    if properties:
        record["properties"] = properties
    if powers:
        record["powers"] = powers

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Parser 5 – Ritual (span.ritualstats)
# ---------------------------------------------------------------------------

def parse_ritual(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1")
    record["name"] = clean(h1.get_text()) if h1 else ""

    # Flavor text in corsivo subito dopo h1
    i_tag = root.find("i")
    if i_tag:
        record["flavor_text"] = clean(i_tag.get_text())

    # Stats: Component Cost, Market Price, Key Skill + Level, Category, Time, Duration
    stats_span = root.find("span", class_="ritualstats")
    if stats_span:
        stats = _parse_br_labels(stats_span)
        record.update(stats)
        # Testo nel p contenitore dopo ritualstats (Level, Category, Time, Duration)
        p = stats_span.find_parent("p")
        if p:
            stats_span.extract()
            remainder = clean(p.get_text(" "))
            # Parsa i campi inline (es. "Level: 1 Category: Creation Time: 1 hour ...")
            for m in re.finditer(r"(Level|Category|Time|Duration)\s*:\s*([^:]+?)(?=Level|Category|Time|Duration|$)", remainder):
                record[m.group(1).lower()] = m.group(2).strip()

    # Descrizione effetto (p senza classe, esclusi quelli che contengono ritualstats)
    stats_keys = {"component_cost", "market_price", "key_skill", "level", "category", "time", "duration"}
    desc_parts: list[str] = []
    for p in root.find_all("p"):
        if not p.get("class") and not p.find("span", class_="ritualstats"):
            text = clean(p.get_text(" "))
            # Evita di duplicare le stats già estratte
            if text and not any(text.startswith(k.replace("_", " ").title()) for k in stats_keys):
                desc_parts.append(text)
    if desc_parts:
        record["description"] = " ".join(desc_parts)

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Parser 6 – Testo libero con poteri embedded (Race, Class, PP, ED, Theme, Trap)
# ---------------------------------------------------------------------------

def parse_freetext(root: Tag) -> tuple[dict, list[str]]:
    record: dict = {}
    h1 = root.find("h1")
    record["name"] = clean(h1.get_text()) if h1 else ""

    # Prerequisito se presente come testo bold "Prerequisite:"
    prereq_match = re.search(r"Prerequisite\s*:\s*(.+?)(?:<br|</|$)", str(root), re.IGNORECASE)
    if prereq_match:
        record["prerequisite"] = clean(BeautifulSoup(prereq_match.group(1), "html.parser").get_text())

    # Poteri embedded (h1.encounterpower ecc.)
    embedded: list[str] = []
    for h in root.find_all("h1")[1:]:
        cls = (h.get("class") or [""])[0]
        if cls in POWER_H1_CLASSES:
            span = h.find("span", class_="level")
            level_text = span.get_text(strip=True) if span else ""
            embedded.append(f"{h.get_text(strip=True)} [{level_text}]" if level_text else h.get_text(strip=True))
    if embedded:
        record["embedded_powers"] = embedded

    # Testo principale (tutto il testo, tolti i tag strutturali)
    # Rimuoviamo i sotto-elementi potere per non duplicare
    root_copy = BeautifulSoup(str(root), "html.parser").find("div", class_="detail")
    if root_copy:
        for tag in root_copy.find_all("h1")[1:]:
            tag.decompose()
        for cls in ("powerstat", "flavor", "publishedIn"):
            for tag in root_copy.find_all("p", class_=cls):
                tag.decompose()
        text = clean(root_copy.get_text(" "))
        # Rimuovi il nome dall'inizio
        name = record.get("name", "")
        if text.startswith(name):
            text = text[len(name):].strip()
        if text:
            record["description"] = text

    record.update(extract_source(root))
    return record, []


# ---------------------------------------------------------------------------
# Router – sceglie il parser giusto
# ---------------------------------------------------------------------------

def detect_and_parse(root: Tag, filepath: Path) -> tuple[dict, list[str]]:
    h1 = root.find("h1")
    if not h1:
        return {"name": root.get("id", filepath.stem)}, ["Nessun h1"]

    h1_class = (h1.get("class") or [""])[0]

    if h1_class in POWER_H1_CLASSES:
        return parse_power(root)

    if h1_class == "monster":
        return parse_monster(root)

    if h1_class in ("mihead", "poison"):
        return parse_magic_item(root)

    if root.find("span", class_="ritualstats"):
        return parse_ritual(root)

    if h1_class == "player":
        # Feat / Deity → p.flavor con <br>-label
        p = root.find("p", class_="flavor") or root.find("p", class_="flavortext")
        if p and p.find("br"):
            return parse_br_labeled(root)
        # Armor → label <b>...</b> e <br> direttamente nel div.detail (fuori dai <p>)
        direct_b = any(
            getattr(c, "name", None) == "b"
            for c in root.children
        )
        if direct_b:
            return parse_root_br_labeled(root)
        # Race / Class / PP / ED / Theme / Glossary / Trap con h1.player
        return parse_freetext(root)

    if h1_class == "dm":   # Trap / Terrain
        return parse_freetext(root)

    return parse_freetext(root)


# ---------------------------------------------------------------------------
# Funzione principale di parsing file
# ---------------------------------------------------------------------------

def parse_file(path: Path) -> tuple[dict | None, list[str]]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_="detail")
    if not root:
        return None, ["Nessun div.detail trovato"]

    record, warnings = detect_and_parse(root, path)
    record["id"] = root.get("id", path.stem)
    # Porta id in testa
    record = {"id": record.pop("id"), **record}
    return record, warnings


# ---------------------------------------------------------------------------
# Elaborazione per categoria
# ---------------------------------------------------------------------------

def process_category(cat_dir: Path, out_root: Path) -> dict:
    cat_name = cat_dir.name
    out_dir = out_root / cat_name
    out_dir.mkdir(parents=True, exist_ok=True)
    unmapped_dir = out_root / "_unmapped" / cat_name

    html_files = sorted(cat_dir.glob("*.html"))
    total = ok = skipped = unmapped_count = 0
    unknown_labels: dict[str, int] = {}

    for html_path in html_files:
        total += 1
        out_path = out_dir / (html_path.stem + ".json")
        if out_path.exists():
            skipped += 1
            continue

        record, warnings = parse_file(html_path)

        if record is None:
            unmapped_count += 1
            unmapped_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(html_path, unmapped_dir / html_path.name)
            print(f"  [{cat_name}] ERRORE {html_path.name}: {warnings}")
            continue

        if warnings:
            unmapped_count += 1
            unmapped_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(html_path, unmapped_dir / html_path.name)
            for w in warnings:
                label = w.split("'")[1] if "'" in w else w
                unknown_labels[label] = unknown_labels.get(label, 0) + 1

        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        ok += 1

    print(f"[{cat_name}] {total} totale | {ok} nuovi | {skipped} già presenti | {unmapped_count} warning")
    return {"total": total, "ok": ok, "skipped": skipped,
            "unmapped": unmapped_count, "labels": unknown_labels}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Parser HTML → JSON per D&D 4e")
    parser.add_argument("--input", default="html_output", help="Cartella HTML di input")
    parser.add_argument("--output", default="json_output", help="Cartella JSON di output")
    parser.add_argument("--category", default=None, help="Singola categoria (es. Power)")
    parser.add_argument("--multithread", action="store_true", help="Parsa le categorie in parallelo")
    args = parser.parse_args()

    in_root = Path(args.input)
    out_root = Path(args.output)

    categories = (
        [in_root / args.category.replace(" ", "_")]
        if args.category
        else sorted(p for p in in_root.iterdir() if p.is_dir() and p.name != "_unmapped")
    )

    if not categories:
        print("Nessuna categoria trovata in", in_root)
        return

    if args.multithread:
        print(f"Avvio parsing parallelo per {len(categories)} categorie...")
        results = []
        with ThreadPoolExecutor(max_workers=len(categories)) as ex:
            futures = {ex.submit(process_category, cat, out_root): cat for cat in categories}
            for fut in as_completed(futures):
                results.append(fut.result())
    else:
        results = [process_category(cat, out_root) for cat in categories]

    total    = sum(r["total"]   for r in results)
    ok       = sum(r["ok"]      for r in results)
    skipped  = sum(r["skipped"] for r in results)
    unmapped = sum(r["unmapped"] for r in results)
    all_labels: dict[str, int] = {}
    for r in results:
        for k, v in r["labels"].items():
            all_labels[k] = all_labels.get(k, 0) + v

    print(f"\n=== RIEPILOGO ===")
    print(f"  Totale: {total} | Nuovi: {ok} | Già presenti: {skipped} | Con warning: {unmapped}")
    if all_labels:
        print(f"\n  Label non mappate ({len(all_labels)} distinte):")
        for label, count in sorted(all_labels.items(), key=lambda x: -x[1]):
            print(f"    '{label}' → {count}x")
    print(f"\nJSON in: {out_root.resolve()}")


if __name__ == "__main__":
    main()
