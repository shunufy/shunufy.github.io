from __future__ import annotations

from pathlib import Path

from db import count_entries, create_entry, find_entries_by_term, init_db, list_entries, search_entries, update_entry


def test_db_create_crud_and_search(tmp_path: Path) -> None:
    db_path = tmp_path / "dictionary.sqlite3"
    init_db(db_path)
    assert count_entries(db_path) == 0

    entry_id = create_entry(
        {
            "term": "雷神",
            "reading": "らいじん",
            "aliases": "Thunder God, 雷の神",
            "language": "Japanese",
            "kind": "神",
            "mythology": "日本",
            "domains": "雷, 嵐",
            "tags": "test, weather",
            "summary": "雷を司る神。",
            "description": "A local storm and thunder deity.",
            "see_also": "トール",
            "sources": "test source",
        },
        db_path,
    )
    assert entry_id > 0
    assert find_entries_by_term("雷神", db_path)[0]["id"] == entry_id

    quick = search_entries("雷", mode="quick", db_path=db_path)
    assert [entry["term"] for entry in quick] == ["雷神"]

    full_text = search_entries("thunder", mode="fts", db_path=db_path)
    assert [entry["term"] for entry in full_text] == ["雷神"]

    fuzzy = search_entries("Thnder God", mode="fuzzy", db_path=db_path)
    assert fuzzy[0]["term"] == "雷神"

    update_entry(
        entry_id,
        {
            "term": "雷神",
            "reading": "らいじん",
            "aliases": "Thunder God",
            "language": "Japanese",
            "kind": "神",
            "mythology": "日本",
            "domains": "雷",
            "tags": "updated",
            "summary": "更新済み。",
            "description": "Updated thunder text.",
            "see_also": "",
            "sources": "",
        },
        db_path,
    )

    updated = search_entries("updated", mode="fts", db_path=db_path)
    assert updated[0]["summary"] == "更新済み。"


def test_multi_value_filters_are_applied_before_result_limit(tmp_path: Path) -> None:
    db_path = tmp_path / "dictionary.sqlite3"
    init_db(db_path)

    for term, tags in [
        ("a雷", "common"),
        ("b雷", "common"),
        ("z雷", "special"),
    ]:
        create_entry(
            {
                "term": term,
                "aliases": "",
                "language": "Japanese",
                "kind": "神",
                "mythology": "日本",
                "domains": "雷",
                "tags": tags,
                "summary": "storm deity",
                "description": "storm deity and thunder figure",
            },
            db_path,
        )

    listed = list_entries(tag_filters=["special"], limit=1, db_path=db_path)
    assert [entry["term"] for entry in listed] == ["z雷"]

    quick = search_entries("雷", mode="quick", tag_filters=["special"], limit=1, db_path=db_path)
    assert [entry["term"] for entry in quick] == ["z雷"]

    full_text = search_entries("storm", mode="fts", tag_filters=["special"], limit=1, db_path=db_path)
    assert [entry["term"] for entry in full_text] == ["z雷"]
