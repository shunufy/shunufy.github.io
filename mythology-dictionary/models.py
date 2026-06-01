from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from typing import Any


ENTRY_FIELDS = [
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
]

LIST_FIELDS = {"aliases", "domains", "tags", "see_also", "sources"}

SCALAR_FIELDS = [field for field in ENTRY_FIELDS if field not in LIST_FIELDS]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_multi_value(value: Any) -> list[str]:
    """Parse a list-like field from JSON array, Python list, or comma-separated text."""
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        items = [clean_text(item) for item in value]
    else:
        text = clean_text(value)
        if not text:
            return []

        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    items = [clean_text(item) for item in parsed]
                else:
                    items = [text]
            except json.JSONDecodeError:
                items = _split_csv_like(text)
        else:
            items = _split_csv_like(text)

    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        item = clean_text(item)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def _split_csv_like(text: str) -> list[str]:
    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", ",")
        .replace("、", ",")
        .replace("；", ";")
        .replace(";", ",")
    )
    try:
        return next(csv.reader([normalized], skipinitialspace=True))
    except csv.Error:
        return normalized.split(",")


def normalize_multi_string(value: Any) -> str:
    return ", ".join(parse_multi_value(value))


def normalize_entry(raw: dict[str, Any], *, require_term: bool = True) -> dict[str, str]:
    entry: dict[str, str] = {}
    for field in ENTRY_FIELDS:
        if field in LIST_FIELDS:
            entry[field] = normalize_multi_string(raw.get(field, ""))
        else:
            entry[field] = clean_text(raw.get(field, ""))

    if require_term and not entry["term"]:
        raise ValueError("term is required")
    return entry


def entry_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    return {key: row[key] for key in row.keys()}


def list_field(entry: dict[str, Any], field: str) -> list[str]:
    return parse_multi_value(entry.get(field, ""))


def merge_multi_values(*values: Any) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in parse_multi_value(value):
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return ", ".join(merged)
