from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from db import (
    DB_PATH,
    find_entries_by_term_in_conn,
    get_connection,
    insert_entry,
    list_entries,
    update_entry_in_conn,
)
from models import ENTRY_FIELDS, LIST_FIELDS, entry_to_dict, merge_multi_values, normalize_entry


EXPORT_FIELDS = ["id", *ENTRY_FIELDS, "created_at", "updated_at"]


def parse_csv_bytes(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_json_bytes(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig").strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL line {line_number} is invalid: {exc}") from exc
        return rows

    if isinstance(parsed, dict) and "entries" in parsed:
        parsed = parsed["entries"]
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [dict(item) for item in parsed]
    raise ValueError("JSON must be an object, a list, or JSONL")


def import_rows(
    rows: list[dict[str, Any]],
    *,
    conflict: str = "skip",
    db_path: str | Path = DB_PATH,
) -> dict[str, Any]:
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    with get_connection(db_path) as conn:
        for index, raw in enumerate(rows, start=1):
            try:
                entry = normalize_entry(raw)
                duplicates = find_entries_by_term_in_conn(conn, entry["term"])

                if not duplicates:
                    insert_entry(conn, entry)
                    stats["created"] += 1
                    continue

                if conflict == "skip":
                    stats["skipped"] += 1
                    continue

                target = duplicates[0]
                if conflict == "overwrite":
                    update_entry_in_conn(conn, target["id"], entry)
                    stats["updated"] += 1
                    continue

                if conflict == "merge_aliases":
                    merged = _merge_into_existing(target, entry)
                    update_entry_in_conn(conn, target["id"], merged)
                    stats["updated"] += 1
                    continue

                raise ValueError(f"Unknown conflict strategy: {conflict}")
            except Exception as exc:
                stats["errors"].append(f"{index}: {exc}")
    return stats


def _merge_into_existing(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {field: existing.get(field, "") for field in ENTRY_FIELDS}
    for field in LIST_FIELDS:
        merged[field] = merge_multi_values(existing.get(field, ""), incoming.get(field, ""))

    for field in ENTRY_FIELDS:
        if field in LIST_FIELDS:
            continue
        if not merged.get(field) and incoming.get(field):
            merged[field] = incoming[field]

    return merged


def export_csv(entries: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry_to_dict(entry))
    return output.getvalue()


def export_json(entries: list[dict[str, Any]]) -> str:
    return json.dumps([entry_to_dict(entry) for entry in entries], ensure_ascii=False, indent=2)


def export_markdown(entries: list[dict[str, Any]]) -> str:
    parts = ["# 用語辞典エクスポート\n"]
    for entry in entries:
        item = entry_to_dict(entry)
        parts.append(f"## {item.get('term', '')}\n")
        metadata = []
        for label, field in (
            ("読み", "reading"),
            ("別名", "aliases"),
            ("言語", "language"),
            ("種別", "kind"),
            ("神話体系", "mythology"),
            ("属性/分野", "domains"),
            ("タグ", "tags"),
        ):
            value = item.get(field, "")
            if value:
                metadata.append(f"- {label}: {value}")
        if metadata:
            parts.append("\n".join(metadata) + "\n")
        if item.get("summary"):
            parts.append(f"\n{item['summary']}\n")
        if item.get("description"):
            parts.append(f"\n{item['description']}\n")
        if item.get("see_also"):
            parts.append(f"\n関連語: {item['see_also']}\n")
        if item.get("sources"):
            parts.append(f"\n出典/参考: {item['sources']}\n")
        parts.append("\n---\n")
    return "\n".join(parts)


def export_all(db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    return list_entries(limit=100000, db_path=db_path)
