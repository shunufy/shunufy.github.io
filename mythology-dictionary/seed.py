from __future__ import annotations

import json
from pathlib import Path

from db import DB_PATH, count_entries, init_db
from import_export import import_rows


BASE_DIR = Path(__file__).resolve().parent
SEED_PATH = BASE_DIR / "data" / "seed.json"


def load_seed_entries(seed_path: str | Path = SEED_PATH) -> list[dict]:
    with Path(seed_path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data.get("entries", [])
    return data


def seed_database(*, db_path: str | Path = DB_PATH, force: bool = False) -> dict:
    init_db(db_path)
    if count_entries(db_path) > 0 and not force:
        return {"created": 0, "updated": 0, "skipped": 0, "errors": [], "message": "database is not empty"}
    entries = load_seed_entries()
    return import_rows(entries, conflict="overwrite" if force else "skip", db_path=db_path)


if __name__ == "__main__":
    result = seed_database(force=False)
    print(result)
