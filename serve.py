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


@app.get("/api/facets")
def facets():
    """Return filterable field values for the given category set."""
    cats = [c.strip() for c in request.args.get("categories", "").split(",") if c.strip()]

    result: dict = {}

    with get_db() as conn:
        if "Power" in cats or not cats:
            base = "FROM entries WHERE category='Power'"
            usage_rows = conn.execute(
                f"SELECT power_type AS v, COUNT(*) n {base} AND power_type IS NOT NULL"
                " GROUP BY power_type ORDER BY n DESC"
            ).fetchall()
            action_rows = conn.execute(
                f"SELECT json_extract(json_data,'$.action_type') AS v, COUNT(*) n {base}"
                " AND json_extract(json_data,'$.action_type') IS NOT NULL"
                " GROUP BY v ORDER BY n DESC LIMIT 12"
            ).fetchall()
            class_rows = conn.execute(
                f"SELECT json_extract(json_data,'$.class_name') AS v, COUNT(*) n {base}"
                " AND json_extract(json_data,'$.class_name') IS NOT NULL"
                " GROUP BY v HAVING n >= 30 ORDER BY n DESC"
            ).fetchall()

            USAGE_LABEL = {"at-will": "At-Will", "encounter": "Encounter", "daily": "Daily"}
            ACTION_LABEL = {
                "Standard Action": "Standard", "Minor Action": "Minor",
                "Immediate Interrupt": "Imm. Interrupt", "Immediate Reaction": "Imm. Reaction",
                "Free Action": "Free", "Move Action": "Move",
                "No Action": "No Action", "Opportunity Action": "Opportunity",
            }
            result["Power"] = {
                "facets": [
                    {
                        "id": "power_usage", "label": "Usage", "type": "badges",
                        "values": [
                            {"value": r["v"], "label": USAGE_LABEL.get(r["v"], r["v"]), "count": r["n"]}
                            for r in usage_rows if r["v"] in USAGE_LABEL
                        ],
                    },
                    {
                        "id": "action_type", "label": "Action", "type": "badges",
                        "values": [
                            {"value": r["v"], "label": ACTION_LABEL.get(r["v"], r["v"]), "count": r["n"]}
                            for r in action_rows if r["v"] in ACTION_LABEL
                        ],
                    },
                    {
                        "id": "class_name", "label": "Class", "type": "badges",
                        "values": [{"value": r["v"], "label": r["v"], "count": r["n"]} for r in class_rows],
                    },
                ]
            }

    return jsonify(result)


@app.get("/api/search")
def search():
    q          = request.args.get("q", "").strip()
    categories = [c.strip() for c in request.args.get("categories", "").split(",") if c.strip()]
    lv_min     = request.args.get("level_min", type=int)
    lv_max     = request.args.get("level_max", type=int)
    page       = max(1, request.args.get("page", 1, type=int))
    per_page   = min(50, request.args.get("per_page", 20, type=int))
    offset     = (page - 1) * per_page

    # Contextual sub-filters
    power_usage  = [v.strip() for v in request.args.get("power_usage",  "").split(",") if v.strip()]
    action_types = [v.strip() for v in request.args.get("action_type",  "").split(",") if v.strip()]
    class_names  = [v.strip() for v in request.args.get("class_name",   "").split(",") if v.strip()]

    params: list = []
    filters: list[str] = []

    if categories:
        placeholders = ",".join("?" * len(categories))
        filters.append(f"e.category IN ({placeholders})")
        params.extend(categories)
    if lv_min is not None:
        filters.append("(e.level >= ? OR e.level IS NULL)")
        params.append(lv_min)
    if lv_max is not None:
        filters.append("(e.level <= ? OR e.level IS NULL)")
        params.append(lv_max)
    if power_usage:
        placeholders = ",".join("?" * len(power_usage))
        filters.append(f"e.power_type IN ({placeholders})")
        params.extend(power_usage)
    if action_types:
        placeholders = ",".join("?" * len(action_types))
        filters.append(f"json_extract(e.json_data,'$.action_type') IN ({placeholders})")
        params.extend(action_types)
    if class_names:
        placeholders = ",".join("?" * len(class_names))
        filters.append(f"json_extract(e.json_data,'$.class_name') IN ({placeholders})")
        params.extend(class_names)

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
