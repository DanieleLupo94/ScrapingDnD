"""
Scraper per iws.mx/dnd - naviga voce per voce e salva screenshot.

Uso:
    python scrape.py [--output DIR] [--category CAT] [--start ID] [--limit N] [--headless] [--multithread]

Esempi:
    python scrape.py --category Power             # solo i Power
    python scrape.py --multithread --headless     # tutte le categorie in parallelo
    python scrape.py --start power6965 --limit 100
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright, Browser

BASE_URL = "https://iws.mx/dnd/"
LIST_URL = BASE_URL + "?list.name.All"

# Categorie conosciute con numero di voci (per info)
ALL_CATEGORIES = [
    "Power", "Monster", "Feat", "Item", "Background", "Trap",
    "Implement", "Weapon", "Paragon Path", "Armor", "Glossary",
    "Ritual", "Companion", "Deity", "Theme", "Epic Destiny",
    "Class", "Disease", "Race", "Poison",
]


async def fetch_ids_by_category(browser: Browser) -> dict[str, list[str]]:
    """Apre una pagina, carica la lista completa e raggruppa gli ID per categoria."""
    page = await browser.new_page(viewport={"width": 1024, "height": 768})
    print("[index] Caricamento indice completo...")
    await page.goto(LIST_URL)
    await page.wait_for_function(
        "window.od?.action?.list?.data?.length > 0",
        timeout=30000,
    )
    result: dict[str, list[str]] = await page.evaluate("""() => {
        const out = {};
        for (const item of window.od.action.list.data) {
            const cat = item._CatName;
            if (!out[cat]) out[cat] = [];
            out[cat].push(item.ID);
        }
        return out;
    }""")
    await page.close()
    total = sum(len(v) for v in result.values())
    print(f"[index] {total} voci in {len(result)} categorie.")
    return result


async def screenshot_entry(page, entry_id: str, out_dir: Path) -> None:
    dest = out_dir / f"{entry_id}.png"
    if dest.exists():
        return
    await page.goto(BASE_URL + f"?view={entry_id}")
    await page.wait_for_selector(f"#{entry_id}", state="visible", timeout=15000)
    element = await page.query_selector(f"#{entry_id}")
    if element:
        await element.screenshot(path=str(dest))
    else:
        await page.screenshot(path=str(dest))


async def scrape_category(
    browser: Browser,
    category: str,
    ids: list[str],
    out_dir: Path,
    limit: int | None,
) -> None:
    """Worker: scarica tutti gli screenshot di una categoria."""
    cat_dir = out_dir / category.replace(" ", "_")
    cat_dir.mkdir(parents=True, exist_ok=True)

    if limit:
        ids = ids[:limit]

    total = len(ids)
    page = await browser.new_page(viewport={"width": 1024, "height": 768})
    done = skipped = errors = 0

    for i, entry_id in enumerate(ids, 1):
        dest = cat_dir / f"{entry_id}.png"
        if dest.exists():
            skipped += 1
            continue
        try:
            await screenshot_entry(page, entry_id, cat_dir)
            done += 1
            if done % 50 == 0 or i == total:
                print(f"[{category}] {i}/{total} — {done} salvati, {skipped} saltati, {errors} errori")
        except Exception as exc:
            errors += 1
            print(f"[{category}] ERRORE {entry_id}: {exc}", file=sys.stderr)

    await page.close()
    print(f"[{category}] COMPLETATO — {done} salvati, {skipped} già presenti, {errors} errori")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper D&D 4e compendium")
    parser.add_argument("--output", default="screenshots", help="Cartella di output")
    parser.add_argument("--category", default=None, help="Singola categoria (es. Power)")
    parser.add_argument("--start", default=None, help="ID da cui partire (solo senza --multithread)")
    parser.add_argument("--limit", type=int, default=None, help="Numero massimo di voci per categoria")
    parser.add_argument("--headless", action="store_true", help="Modalità senza finestra")
    parser.add_argument("--multithread", action="store_true", help="Un browser per categoria, in parallelo")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        if args.multithread:
            # --- modalità parallela ---
            # Un browser di servizio per scaricare l'indice, poi uno per categoria
            index_browser = await pw.chromium.launch(headless=args.headless)
            ids_by_cat = await fetch_ids_by_category(index_browser)
            await index_browser.close()

            # Filtra categoria se richiesta
            if args.category:
                if args.category not in ids_by_cat:
                    print(f"Categoria '{args.category}' non trovata. Disponibili: {sorted(ids_by_cat)}")
                    return
                ids_by_cat = {args.category: ids_by_cat[args.category]}

            categories = list(ids_by_cat.keys())
            print(f"Avvio {len(categories)} browser in parallelo: {categories}")

            async def run_worker(cat: str) -> None:
                browser = await pw.chromium.launch(headless=args.headless)
                await scrape_category(browser, cat, ids_by_cat[cat], out_dir, args.limit)
                await browser.close()

            await asyncio.gather(*[run_worker(cat) for cat in categories])

        else:
            # --- modalità singola (comportamento originale) ---
            browser = await pw.chromium.launch(headless=args.headless)
            page = await browser.new_page(viewport={"width": 1024, "height": 768})

            print("Caricamento lista in corso...")
            await page.goto(LIST_URL)
            await page.wait_for_function(
                "window.od?.action?.list?.data?.length > 0",
                timeout=30000,
            )
            ids: list[str] = await page.evaluate(
                """(category) => {
                    const data = window.od.action.list.data;
                    return data
                        .filter(item => !category || item._CatName === category)
                        .map(item => item.ID);
                }""",
                args.category,
            )
            cat_label = f" per categoria '{args.category}'" if args.category else ""
            print(f"Trovate {len(ids)} voci{cat_label}.")

            if args.start and args.start in ids:
                idx = ids.index(args.start)
                ids = ids[idx:]
                print(f"Partenza da indice {idx}: {args.start}")

            if args.limit:
                ids = ids[: args.limit]

            cat_dir = out_dir / (args.category.replace(" ", "_") if args.category else "All")
            cat_dir.mkdir(parents=True, exist_ok=True)
            total = len(ids)
            print(f"Voci da scaricare: {total}")

            for i, entry_id in enumerate(ids, 1):
                dest = cat_dir / f"{entry_id}.png"
                if dest.exists():
                    print(f"[{i}/{total}] {entry_id} — già presente, salto")
                    continue
                try:
                    await screenshot_entry(page, entry_id, cat_dir)
                    print(f"[{i}/{total}] {entry_id} — salvato")
                except Exception as exc:
                    print(f"[{i}/{total}] {entry_id} — ERRORE: {exc}", file=sys.stderr)

            await browser.close()

    print(f"\nFatto! Screenshot in: {out_dir.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
