"""
Server di ricerca per il compendium D&D 4e.

Uso:
    python serve.py [--db FILE] [--port N]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")
DB_PATH = "dnd.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/categories")
def categories():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) as n FROM entries GROUP BY category ORDER BY category"
        ).fetchall()
    return jsonify([{"name": r["category"], "count": r["n"]} for r in rows])


@app.get("/api/search")
def search():
    q        = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    lv_min   = request.args.get("level_min", type=int)
    lv_max   = request.args.get("level_max", type=int)
    page     = max(1, request.args.get("page", 1, type=int))
    per_page = min(50, request.args.get("per_page", 20, type=int))
    offset   = (page - 1) * per_page

    params: list = []
    filters: list[str] = []

    if category:
        filters.append("e.category = ?")
        params.append(category)
    if lv_min is not None:
        filters.append("(e.level >= ? OR e.level IS NULL)")
        params.append(lv_min)
    if lv_max is not None:
        filters.append("(e.level <= ? OR e.level IS NULL)")
        params.append(lv_max)

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with get_db() as conn:
        if q:
            # FTS5: i termini multi-parola vengono matchati come frase con ""
            fts_q = f'"{q}"' if " " in q else q + "*"
            count_sql = f"""
                SELECT COUNT(*) FROM entries_fts
                JOIN entries e ON entries_fts.rowid = e.rowid
                {where}
                AND entries_fts MATCH ?
            """
            total = conn.execute(count_sql, params + [fts_q]).fetchone()[0]

            rows_sql = f"""
                SELECT e.id, e.name, e.category, e.level, e.power_type,
                       e.json_data,
                       bm25(entries_fts) AS score
                FROM entries_fts
                JOIN entries e ON entries_fts.rowid = e.rowid
                {where}
                AND entries_fts MATCH ?
                ORDER BY score
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(rows_sql, params + [fts_q, per_page, offset]).fetchall()
        else:
            count_sql = f"SELECT COUNT(*) FROM entries e {where}"
            total = conn.execute(count_sql, params).fetchone()[0]

            rows_sql = f"""
                SELECT e.id, e.name, e.category, e.level, e.power_type, e.json_data
                FROM entries e
                {where}
                ORDER BY e.name
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(rows_sql, params + [per_page, offset]).fetchall()

    results = []
    for r in rows:
        data = json.loads(r["json_data"])
        results.append({
            "id":         r["id"],
            "name":       r["name"],
            "category":   r["category"],
            "level":      r["level"],
            "power_type": r["power_type"],
            "data":       data,
        })

    return jsonify({
        "total":   total,
        "page":    page,
        "pages":   (total + per_page - 1) // per_page,
        "results": results,
    })


@app.get("/api/entry/<entry_id>")
def entry(entry_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM entries WHERE id = ?", (entry_id,)
        ).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "id":       row["id"],
        "name":     row["name"],
        "category": row["category"],
        "level":    row["level"],
        "data":     json.loads(row["json_data"]),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db",   default=os.environ.get("DB_PATH", "dnd.db"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", 8080)), type=int)
    args = parser.parse_args()

    global DB_PATH
    DB_PATH = args.db

    if not Path(DB_PATH).exists():
        print(f"DB not found: {DB_PATH}")
        print("Run first: python build_db.py")
        return

    print(f"Starting on http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
