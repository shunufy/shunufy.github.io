from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "dictionary.sqlite3"
MIN_ENTRY_COUNT = 1000
REQUIRED_COLUMNS = {
    "id",
    "term",
    "reading",
    "aliases",
    "language",
    "kind",
    "mythology",
    "domains",
    "tags",
    "summary",
    "description",
    "see_also",
    "sources",
    "created_at",
    "updated_at",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_database() -> None:
    if not DB_PATH.exists():
        fail(f"Missing database: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()}
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            fail(f"entries table is missing columns: {', '.join(missing)}")

        count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        if count < MIN_ENTRY_COUNT:
            fail(f"Expected at least {MIN_ENTRY_COUNT} entries, found {count}")

        blank_terms = conn.execute("SELECT COUNT(*) FROM entries WHERE TRIM(term) = ''").fetchone()[0]
        if blank_terms:
            fail(f"Found {blank_terms} rows with blank terms")

        fts_count = conn.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
        if fts_count != count:
            fail(f"FTS index count mismatch: entries={count}, entries_fts={fts_count}")

        sample = conn.execute(
            """
            SELECT e.term
            FROM entries_fts
            JOIN entries e ON e.id = entries_fts.rowid
            WHERE entries_fts MATCH 'Yggdrasil OR Ragnarok OR Zeus'
            LIMIT 1
            """
        ).fetchone()
        if sample is None:
            fail("FTS sample query returned no rows")

        print(f"Database OK: {count} entries, FTS rows={fts_count}")


def check_json_files() -> None:
    data_dir = ROOT / "data"
    json_files = sorted(data_dir.glob("*.json")) + sorted((ROOT / "言語ファイル").glob("*.json"))
    for path in json_files:
        with path.open("r", encoding="utf-8-sig") as handle:
            json.load(handle)
    print(f"JSON OK: {len(json_files)} files")


def main() -> int:
    check_database()
    check_json_files()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

