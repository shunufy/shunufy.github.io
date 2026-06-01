from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from models import ENTRY_FIELDS, LIST_FIELDS, entry_to_dict, list_field, normalize_entry, now_iso


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "dictionary.sqlite3"


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                reading TEXT NOT NULL DEFAULT '',
                aliases TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL DEFAULT '',
                mythology TEXT NOT NULL DEFAULT '',
                domains TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                see_also TEXT NOT NULL DEFAULT '',
                sources TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entries_term ON entries(term);
            CREATE INDEX IF NOT EXISTS idx_entries_reading ON entries(reading);
            CREATE INDEX IF NOT EXISTS idx_entries_language ON entries(language);
            CREATE INDEX IF NOT EXISTS idx_entries_kind ON entries(kind);
            CREATE INDEX IF NOT EXISTS idx_entries_mythology ON entries(mythology);

            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                term,
                aliases,
                summary,
                description,
                content='entries',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                INSERT INTO entries_fts(rowid, term, aliases, summary, description)
                VALUES (new.id, new.term, new.aliases, new.summary, new.description);
            END;

            CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                INSERT INTO entries_fts(entries_fts, rowid, term, aliases, summary, description)
                VALUES ('delete', old.id, old.term, old.aliases, old.summary, old.description);
            END;

            CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                INSERT INTO entries_fts(entries_fts, rowid, term, aliases, summary, description)
                VALUES ('delete', old.id, old.term, old.aliases, old.summary, old.description);
                INSERT INTO entries_fts(rowid, term, aliases, summary, description)
                VALUES (new.id, new.term, new.aliases, new.summary, new.description);
            END;
            """
        )
        _rebuild_fts_if_needed(conn)


def _rebuild_fts_if_needed(conn: sqlite3.Connection) -> None:
    entry_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
    if entry_count != fts_count:
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES ('rebuild')")


def rebuild_fts(db_path: str | Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES ('rebuild')")


def count_entries(db_path: str | Path = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0])


def insert_entry(conn: sqlite3.Connection, data: dict[str, Any]) -> int:
    entry = normalize_entry(data)
    now = now_iso()
    entry["created_at"] = data.get("created_at") or now
    entry["updated_at"] = data.get("updated_at") or now

    columns = ENTRY_FIELDS + ["created_at", "updated_at"]
    placeholders = ", ".join(f":{column}" for column in columns)
    sql = f"INSERT INTO entries ({', '.join(columns)}) VALUES ({placeholders})"
    cursor = conn.execute(sql, entry)
    return int(cursor.lastrowid)


def create_entry(data: dict[str, Any], db_path: str | Path = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        return insert_entry(conn, data)


def update_entry_in_conn(conn: sqlite3.Connection, entry_id: int, data: dict[str, Any]) -> None:
    current = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if current is None:
        raise KeyError(f"Entry id={entry_id} was not found")

    entry = normalize_entry(data)
    entry["id"] = entry_id
    entry["updated_at"] = now_iso()
    assignments = ", ".join(f"{field} = :{field}" for field in ENTRY_FIELDS)
    conn.execute(
        f"UPDATE entries SET {assignments}, updated_at = :updated_at WHERE id = :id",
        entry,
    )


def update_entry(entry_id: int, data: dict[str, Any], db_path: str | Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        update_entry_in_conn(conn, entry_id, data)


def delete_entry(entry_id: int, db_path: str | Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))


def get_entry(entry_id: int, db_path: str | Path = DB_PATH) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return entry_to_dict(row) if row else None


def find_entries_by_term_in_conn(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    normalized = term.strip()
    rows = conn.execute(
        "SELECT * FROM entries WHERE term = ? COLLATE NOCASE ORDER BY updated_at DESC, id DESC",
        (normalized,),
    ).fetchall()
    return [entry_to_dict(row) for row in rows]


def find_entries_by_term(term: str, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        return find_entries_by_term_in_conn(conn, term)


def get_entry_by_term(term: str, db_path: str | Path = DB_PATH) -> dict[str, Any] | None:
    matches = find_entries_by_term(term, db_path)
    return matches[0] if matches else None


def random_entry(db_path: str | Path = DB_PATH) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM entries ORDER BY RANDOM() LIMIT 1").fetchone()
        return entry_to_dict(row) if row else None


def get_filter_values(field: str, db_path: str | Path = DB_PATH) -> list[str]:
    if field not in set(ENTRY_FIELDS) | {"created_at", "updated_at"}:
        raise ValueError(f"Unknown field: {field}")

    with get_connection(db_path) as conn:
        if field in LIST_FIELDS:
            rows = conn.execute(f"SELECT {field} FROM entries WHERE {field} != ''").fetchall()
            values: set[str] = set()
            for row in rows:
                values.update(list_field(entry_to_dict(row), field))
            return sorted(values, key=str.casefold)

        rows = conn.execute(
            f"SELECT DISTINCT {field} FROM entries WHERE {field} != '' ORDER BY {field}"
        ).fetchall()
        return [row[0] for row in rows]


def list_entries(
    *,
    filters: dict[str, str] | None = None,
    tag_filters: list[str] | None = None,
    domain_filters: list[str] | None = None,
    limit: int = 500,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    where, params = _scalar_where(filters)
    has_multi_filters = bool(tag_filters or domain_filters)
    sql = f"SELECT * FROM entries WHERE {where} ORDER BY term COLLATE NOCASE"
    if not has_multi_filters:
        sql += " LIMIT :limit"
        params = {**params, "limit": limit}

    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    filtered = _apply_multi_filters([entry_to_dict(row) for row in rows], tag_filters, domain_filters)
    return filtered[:limit]


def search_entries(
    query: str = "",
    *,
    mode: str = "quick",
    filters: dict[str, str] | None = None,
    tag_filters: list[str] | None = None,
    domain_filters: list[str] | None = None,
    limit: int = 100,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    query = query.strip()
    if mode == "fts":
        return search_full_text(query, filters, tag_filters, domain_filters, limit, db_path)
    if mode == "fuzzy":
        return search_fuzzy(query, filters, tag_filters, domain_filters, limit, db_path)
    return search_quick(query, filters, tag_filters, domain_filters, limit, db_path)


def search_quick(
    query: str,
    filters: dict[str, str] | None,
    tag_filters: list[str] | None,
    domain_filters: list[str] | None,
    limit: int,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    where, params = _scalar_where(filters)
    if query:
        params.update({"q": query, "like": f"%{query}%", "prefix": f"{query}%"})
        where = (
            f"{where} AND (term LIKE :like COLLATE NOCASE "
            "OR reading LIKE :like COLLATE NOCASE "
            "OR aliases LIKE :like COLLATE NOCASE)"
        )
        order = """
            CASE
                WHEN term = :q COLLATE NOCASE THEN 0
                WHEN term LIKE :prefix COLLATE NOCASE THEN 1
                WHEN reading LIKE :prefix COLLATE NOCASE THEN 2
                WHEN aliases LIKE :like COLLATE NOCASE THEN 3
                ELSE 4
            END,
            term COLLATE NOCASE
        """
    else:
        order = "term COLLATE NOCASE"

    has_multi_filters = bool(tag_filters or domain_filters)
    sql = f"SELECT * FROM entries WHERE {where} ORDER BY {order}"
    exec_params = dict(params)
    if not has_multi_filters:
        sql += " LIMIT :limit"
        exec_params["limit"] = limit

    with get_connection(db_path) as conn:
        rows = conn.execute(sql, exec_params).fetchall()
    filtered = _apply_multi_filters([entry_to_dict(row) for row in rows], tag_filters, domain_filters)
    return filtered[:limit]


def search_full_text(
    query: str,
    filters: dict[str, str] | None,
    tag_filters: list[str] | None,
    domain_filters: list[str] | None,
    limit: int,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    if not query:
        return list_entries(
            filters=filters,
            tag_filters=tag_filters,
            domain_filters=domain_filters,
            limit=limit,
            db_path=db_path,
        )

    where, params = _scalar_where(filters, table_alias="e")
    fts_query = _make_fts_query(query)
    rows: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    has_multi_filters = bool(tag_filters or domain_filters)
    fts_limit_clause = "" if has_multi_filters else "LIMIT :limit"
    fts_params = dict(params)
    if not has_multi_filters:
        fts_params["limit"] = limit

    with get_connection(db_path) as conn:
        try:
            fts_rows = conn.execute(
                f"""
                SELECT e.*, bm25(entries_fts) AS search_rank
                FROM entries_fts
                JOIN entries e ON e.id = entries_fts.rowid
                WHERE entries_fts MATCH :fts_query AND {where}
                ORDER BY search_rank
                {fts_limit_clause}
                """,
                {**fts_params, "fts_query": fts_query},
            ).fetchall()
        except sqlite3.OperationalError:
            fts_rows = []

        for row in fts_rows:
            entry = entry_to_dict(row)
            seen_ids.add(entry["id"])
            rows.append(entry)

        like_where, like_params = _scalar_where(filters, table_alias="e")
        like_params["like"] = f"%{query}%"
        like_limit_clause = "" if has_multi_filters else "LIMIT :limit"
        if not has_multi_filters:
            like_params["limit"] = limit
        fallback_rows = conn.execute(
            f"""
            SELECT e.*
            FROM entries e
            WHERE {like_where}
              AND (
                e.term LIKE :like COLLATE NOCASE
                OR e.aliases LIKE :like COLLATE NOCASE
                OR e.summary LIKE :like COLLATE NOCASE
                OR e.description LIKE :like COLLATE NOCASE
              )
            ORDER BY e.term COLLATE NOCASE
            {like_limit_clause}
            """,
            like_params,
        ).fetchall()

    for row in fallback_rows:
        entry = entry_to_dict(row)
        if entry["id"] in seen_ids:
            continue
        rows.append(entry)
        seen_ids.add(entry["id"])

    return _apply_multi_filters(rows, tag_filters, domain_filters)[:limit]


def search_fuzzy(
    query: str,
    filters: dict[str, str] | None,
    tag_filters: list[str] | None,
    domain_filters: list[str] | None,
    limit: int,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    candidates = list_entries(
        filters=filters,
        tag_filters=tag_filters,
        domain_filters=domain_filters,
        limit=5000,
        db_path=db_path,
    )
    if not query:
        return candidates[:limit]

    scored = []
    for entry in candidates:
        score = _fuzzy_score(query, entry)
        if score >= 45:
            entry = dict(entry)
            entry["fuzzy_score"] = score
            scored.append(entry)

    scored.sort(key=lambda item: (-item["fuzzy_score"], item["term"].casefold()))
    return scored[:limit]


def _scalar_where(
    filters: dict[str, str] | None,
    *,
    table_alias: str | None = None,
) -> tuple[str, dict[str, str]]:
    prefix = f"{table_alias}." if table_alias else ""
    clauses = ["1 = 1"]
    params: dict[str, str] = {}
    for field in ("mythology", "kind", "language"):
        value = (filters or {}).get(field, "").strip()
        if value:
            clauses.append(f"{prefix}{field} = :filter_{field}")
            params[f"filter_{field}"] = value
    return " AND ".join(clauses), params


def _apply_multi_filters(
    rows: list[dict[str, Any]],
    tag_filters: list[str] | None,
    domain_filters: list[str] | None,
) -> list[dict[str, Any]]:
    tag_filters = tag_filters or []
    domain_filters = domain_filters or []
    if not tag_filters and not domain_filters:
        return rows

    filtered = []
    for row in rows:
        tags = {value.casefold() for value in list_field(row, "tags")}
        domains = {value.casefold() for value in list_field(row, "domains")}
        if tag_filters and not all(tag.casefold() in tags for tag in tag_filters):
            continue
        if domain_filters and not all(domain.casefold() in domains for domain in domain_filters):
            continue
        filtered.append(row)
    return filtered


def _make_fts_query(query: str) -> str:
    tokens = re.findall(r"[\w\u3040-\u30ff\u3400-\u9fff\u4e00-\u9fff]+", query, flags=re.UNICODE)
    if not tokens:
        tokens = [query]
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)


def _fuzzy_score(query: str, entry: dict[str, Any]) -> float:
    targets = [
        entry.get("term", ""),
        entry.get("reading", ""),
        entry.get("summary", ""),
        *list_field(entry, "aliases"),
        *list_field(entry, "tags"),
        *list_field(entry, "domains"),
    ]
    targets = [target for target in targets if target]
    if not targets:
        return 0.0

    try:
        from rapidfuzz import fuzz

        return max(float(fuzz.WRatio(query, target)) for target in targets)
    except Exception:
        from difflib import SequenceMatcher

    return max(SequenceMatcher(None, query.casefold(), target.casefold()).ratio() * 100 for target in targets)


def find_related_entries(
    entry_id: int,
    *,
    limit: int = 8,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    """Return entries that share useful dictionary facets with the selected entry."""
    with get_connection(db_path) as conn:
        base_row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if base_row is None:
            return []
        rows = conn.execute("SELECT * FROM entries WHERE id != ?", (entry_id,)).fetchall()

    base = entry_to_dict(base_row)
    base_domains = {value.casefold() for value in list_field(base, "domains")}
    base_tags = {value.casefold() for value in list_field(base, "tags")}
    base_see_also = {value.casefold() for value in list_field(base, "see_also")}
    base_mythology = str(base.get("mythology", "")).casefold()
    base_kind = str(base.get("kind", "")).casefold()

    scored: list[tuple[int, str, dict[str, Any]]] = []
    for row in rows:
        entry = entry_to_dict(row)
        score = 0
        reasons: list[str] = []

        mythology = str(entry.get("mythology", "")).casefold()
        kind = str(entry.get("kind", "")).casefold()
        domains = {value.casefold() for value in list_field(entry, "domains")}
        tags = {value.casefold() for value in list_field(entry, "tags")}
        aliases = {value.casefold() for value in list_field(entry, "aliases")}
        names = {str(entry.get("term", "")).casefold(), *aliases}

        if base_mythology and mythology == base_mythology:
            score += 3
            reasons.append("同じ神話圏")
        if base_kind and kind == base_kind:
            score += 2
            reasons.append("同じ種別")

        shared_domains = sorted(base_domains & domains)
        if shared_domains:
            score += min(5, len(shared_domains) * 2)
            reasons.append("同じ属性")

        shared_tags = sorted(base_tags & tags)
        if shared_tags:
            score += min(3, len(shared_tags))
            reasons.append("同じタグ")

        if base_see_also & names:
            score += 8
            reasons.append("関連語")

        if score <= 0:
            continue

        entry = dict(entry)
        entry["related_score"] = score
        entry["related_reason"] = " / ".join(dict.fromkeys(reasons))
        scored.append((score, str(entry.get("term", "")).casefold(), entry))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [entry for _, _, entry in scored[:limit]]


def quality_stats(db_path: str | Path = DB_PATH) -> dict[str, int]:
    with get_connection(db_path) as conn:
        rows = [entry_to_dict(row) for row in conn.execute("SELECT * FROM entries").fetchall()]

    return {
        "total": len(rows),
        "short_description": sum(1 for row in rows if len(str(row.get("description", "")).strip()) < 180),
        "missing_english": sum(1 for row in rows if not _has_english_alias(row)),
        "missing_see_also": sum(1 for row in rows if not list_field(row, "see_also")),
        "missing_sources": sum(1 for row in rows if not list_field(row, "sources")),
    }


def list_quality_entries(
    issue: str,
    *,
    limit: int = 100,
    db_path: str | Path = DB_PATH,
) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = [entry_to_dict(row) for row in conn.execute("SELECT * FROM entries ORDER BY term COLLATE NOCASE").fetchall()]

    if issue == "short_description":
        filtered = [row for row in rows if len(str(row.get("description", "")).strip()) < 180]
    elif issue == "missing_english":
        filtered = [row for row in rows if not _has_english_alias(row)]
    elif issue == "missing_see_also":
        filtered = [row for row in rows if not list_field(row, "see_also")]
    elif issue == "missing_sources":
        filtered = [row for row in rows if not list_field(row, "sources")]
    else:
        filtered = []
    return filtered[:limit]


def _has_english_alias(entry: dict[str, Any]) -> bool:
    return any(re.search(r"[A-Za-z]", alias) for alias in list_field(entry, "aliases"))
