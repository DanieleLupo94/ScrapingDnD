"""
Costruisce dnd.db da json_output/.

Uso:
    python build_db.py [--input DIR] [--db FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


def flatten_text(obj, _depth=0) -> str:
    """Appiattisce ricorsivamente un oggetto JSON in testo ricercabile."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        return " ".join(flatten_text(v, _depth + 1) for v in obj)
    if isinstance(obj, dict):
        return " ".join(flatten_text(v, _depth + 1) for v in obj.values())
    return ""


def extract_level(record: dict) -> int | None:
    lv = record.get("level")
    if isinstance(lv, int):
        return lv
    if isinstance(lv, str):
        m = re.search(r"\d+", lv)
        if m:
            return int(m.group())
    # Prova level_line (Disease)
    ll = record.get("level_line", "")
    m = re.search(r"\d+", str(ll))
    if m:
        return int(m.group())
    # Item / Weapon / Implement: "Level 12 Uncommon"
    il = record.get("item_level", "")
    m = re.search(r"\d+", str(il))
    if m:
        return int(m.group())
    return None


def build(input_dir: Path, db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        DROP TABLE IF EXISTS entries_fts;
        DROP TABLE IF EXISTS entries;

        CREATE TABLE entries (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL,
            level       INTEGER,
            power_type  TEXT,
            json_data   TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE entries_fts USING fts5(
            name,
            full_text,
            content=entries,
            content_rowid=rowid,
            tokenize='unicode61 remove_diacritics 1'
        );
    """)

    rows: list[tuple] = []
    categories = sorted(p for p in input_dir.iterdir() if p.is_dir() and not p.name.startswith("_"))

    for cat_dir in categories:
        category = cat_dir.name.replace("_", " ")
        for json_path in sorted(cat_dir.glob("*.json")):
            try:
                record = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            entry_id   = record.get("id", json_path.stem)
            name       = record.get("name", "")
            level      = extract_level(record)
            power_type = record.get("power_type") or record.get("usage") or None
            full_text  = flatten_text(record)

            rows.append((entry_id, name, category, level, power_type,
                         json.dumps(record, ensure_ascii=False), full_text))

    conn.executemany(
        "INSERT INTO entries(id, name, category, level, power_type, json_data) VALUES (?,?,?,?,?,?)",
        [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows],
    )
    conn.executemany(
        "INSERT INTO entries_fts(rowid, name, full_text) "
        "SELECT rowid, name, ? FROM entries WHERE id = ?",
        [(r[6], r[0]) for r in rows],
    )

    # Indici per i filtri comuni
    conn.executescript("""
        CREATE INDEX idx_category ON entries(category);
        CREATE INDEX idx_level    ON entries(level);
    """)
    conn.commit()
    conn.close()

    total = len(rows)
    print(f"DB built: {db_path}  ({total} entries)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="json_output")
    parser.add_argument("--db",    default="dnd.db")
    args = parser.parse_args()
    build(Path(args.input), Path(args.db))


if __name__ == "__main__":
    main()
