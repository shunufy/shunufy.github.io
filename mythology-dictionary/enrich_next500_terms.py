from __future__ import annotations

from pathlib import Path

import enrich_next200_terms as base
from db import DB_PATH


base.INPUT_PATH = Path("data/next500_before_enrich.json")
base.OUT_PATH = Path("data/next500_enriched_terms.json")
base.BACKUP_PATH = DB_PATH.with_name("dictionary.before_next500_enrichment.sqlite3")
base.TAG = "次500補筆"
base.SOURCE_NOTE = "既存データをもとに辞典向けに補筆"


if __name__ == "__main__":
    base.main()
