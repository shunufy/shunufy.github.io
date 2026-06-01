from __future__ import annotations

from pathlib import Path
import re

import streamlit as st

from db import (
    DB_PATH,
    count_entries,
    create_entry,
    delete_entry,
    find_entries_by_term,
    find_related_entries,
    get_entry,
    get_entry_by_term,
    get_filter_values,
    init_db,
    list_entries,
    list_quality_entries,
    quality_stats,
    random_entry,
    rebuild_fts,
    search_entries,
    update_entry,
)
from import_export import (
    export_all,
    export_csv,
    export_json,
    export_markdown,
    import_rows,
    parse_csv_bytes,
    parse_json_bytes,
)
from models import ENTRY_FIELDS, list_field
from seed import seed_database


st.set_page_config(page_title="用語辞典", page_icon="辞", layout="wide")


FIELD_LABELS = {
    "term": "見出し語",
    "reading": "読み/かな",
    "aliases": "別名",
    "language": "言語",
    "kind": "種別",
    "mythology": "神話体系",
    "domains": "属性/分野",
    "tags": "タグ",
    "summary": "短い説明",
    "description": "詳説",
    "see_also": "関連語",
    "sources": "出典/参考",
}

SEARCH_MODES = {
    "クイック": "quick",
    "全文": "fts",
    "あいまい": "fuzzy",
}

PAGES = ["検索", "追加", "逆引き", "入出力", "管理"]
DEFAULT_PREVIEW_LIMIT = 30
SEARCH_RESULT_LIMIT = 100
REVERSE_RESULT_LIMIT = 100
RELATED_RESULT_LIMIT = 8
FILTER_DEFAULT_LIMIT = 45
FILTER_SEARCH_LIMIT = 120

CONFLICT_MODES = {
    "スキップ": "skip",
    "上書き": "overwrite",
    "別名追加": "merge_aliases",
}


def main() -> None:
    bootstrap()
    ensure_state()

    st.title("用語辞典")

    filters, tag_filters, domain_filters = render_sidebar()

    page = st.radio("画面", PAGES, horizontal=True, label_visibility="collapsed", key="active_page")

    if page == "検索":
        render_search(filters, tag_filters, domain_filters)
    elif page == "追加":
        render_add()
    elif page == "逆引き":
        render_reverse_lookup()
    elif page == "入出力":
        render_import_export()
    else:
        render_manage()


def bootstrap() -> None:
    init_db(DB_PATH)
    if count_entries(DB_PATH) == 0:
        seed_database(db_path=DB_PATH, force=False)


def ensure_state() -> None:
    st.session_state.setdefault("selected_id", None)
    st.session_state.setdefault("search_query", "")
    st.session_state.setdefault("applied_search_query", "")


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    st.experimental_rerun()


def render_sidebar() -> tuple[dict[str, str], list[str], list[str]]:
    st.sidebar.header("絞り込み")
    signature = db_signature()
    mythologies = cached_filter_values("mythology", signature)
    kinds = cached_filter_values("kind", signature)
    languages = cached_filter_values("language", signature)
    domains = cached_filter_values("domains", signature)
    tags = cached_filter_values("tags", signature)

    option_query = st.sidebar.text_input(
        "候補を絞る",
        key="sidebar_filter_query",
        placeholder="例: イスラム / 天使 / 冥界",
    ).strip()
    mythology = render_scalar_filter(
        st.sidebar, "神話体系", mythologies, "sidebar_mythology", option_query
    )
    kind = render_scalar_filter(st.sidebar, "種別", kinds, "sidebar_kind", option_query)
    language = render_scalar_filter(st.sidebar, "言語", languages, "sidebar_language", option_query)
    domain_filters = render_multi_filter(
        st.sidebar, "属性/分野", domains, "sidebar_domains", option_query
    )
    tag_filters = render_multi_filter(st.sidebar, "タグ", tags, "sidebar_tags", option_query)
    render_active_filter_summary(st.sidebar, mythology, kind, language, domain_filters, tag_filters)

    st.sidebar.button(
        "絞り込みをリセット",
        use_container_width=True,
        on_click=reset_filter_state,
        args=("sidebar",),
    )

    if st.sidebar.button("ランダムに1件", use_container_width=True):
        entry = random_entry(DB_PATH)
        if entry:
            st.session_state.selected_id = entry["id"]
            rerun()

    filters = {"mythology": mythology, "kind": kind, "language": language}
    return filters, tag_filters, domain_filters


def render_scalar_filter(
    container,
    label: str,
    options: list[str],
    key: str,
    option_query: str,
) -> str:
    current = st.session_state.get(key, "")
    visible_options = compact_filter_options(options, option_query, [current])
    return container.selectbox(
        label,
        [""] + visible_options,
        format_func=lambda value: value or "すべて",
        key=key,
    )


def render_multi_filter(
    container,
    label: str,
    options: list[str],
    key: str,
    option_query: str,
) -> list[str]:
    current = st.session_state.get(key, [])
    visible_options = compact_filter_options(options, option_query, current)
    selected = container.multiselect(label, visible_options, key=key)
    shown = len(visible_options)
    total = len(options)
    if option_query:
        container.caption(f"{label}: {shown}/{total}件を表示")
    elif total > shown:
        container.caption(f"{label}: 先頭{shown}件を表示。候補検索で絞れます。")
    return selected


def compact_filter_options(
    options: list[str],
    option_query: str,
    selected: list[str] | tuple[str, ...],
) -> list[str]:
    query = option_query.casefold()
    selected_values = [value for value in selected if value]
    if query:
        matches = [value for value in options if query in value.casefold()]
        limit = FILTER_SEARCH_LIMIT
    else:
        matches = options
        limit = FILTER_DEFAULT_LIMIT

    compacted: list[str] = []
    seen: set[str] = set()
    for value in selected_values + matches[:limit]:
        if value and value not in seen:
            compacted.append(value)
            seen.add(value)
    return compacted


def render_active_filter_summary(
    container,
    mythology: str,
    kind: str,
    language: str,
    domain_filters: list[str],
    tag_filters: list[str],
) -> None:
    active = []
    if mythology:
        active.append(f"神話体系={mythology}")
    if kind:
        active.append(f"種別={kind}")
    if language:
        active.append(f"言語={language}")
    active.extend(f"属性={value}" for value in domain_filters)
    active.extend(f"タグ={value}" for value in tag_filters)
    container.caption("選択中: " + " / ".join(active) if active else "絞り込みなし")


def reset_filter_state(prefix: str) -> None:
    defaults = {
        f"{prefix}_filter_query": "",
        f"{prefix}_mythology": "",
        f"{prefix}_kind": "",
        f"{prefix}_language": "",
        f"{prefix}_domains": [],
        f"{prefix}_tags": [],
    }
    for key, value in defaults.items():
        st.session_state[key] = value


def db_signature() -> int:
    try:
        return DB_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


@st.cache_data(show_spinner=False)
def cached_filter_values(field: str, signature: int) -> list[str]:
    return get_filter_values(field, DB_PATH)


def render_search(filters: dict[str, str], tag_filters: list[str], domain_filters: list[str]) -> None:
    param_query = current_query_param("q")
    if param_query and st.session_state.get("search_query") != param_query:
        st.session_state.search_query = param_query
        st.session_state.applied_search_query = param_query
        st.session_state.selected_id = None

    top_cols = st.columns([3, 1])
    with top_cols[0]:
        st.text_input("検索語", key="search_query")
        search_col, clear_col = st.columns([3, 1])
        with search_col:
            st.button("検索", key="run_search", use_container_width=True, on_click=apply_search_query)
        with clear_col:
            st.button("クリア", key="clear_search", use_container_width=True, on_click=clear_search_query)
    with top_cols[1]:
        mode_label = st.radio("検索方式", list(SEARCH_MODES.keys()), horizontal=True)

    if st.session_state.selected_id:
        render_detail(st.session_state.selected_id)
        st.divider()

    active_query = st.session_state.applied_search_query
    active_filters = has_active_filters(filters, tag_filters, domain_filters)
    limit = SEARCH_RESULT_LIMIT if active_query or active_filters else DEFAULT_PREVIEW_LIMIT
    results = search_entries(
        active_query,
        mode=SEARCH_MODES[mode_label],
        filters=filters,
        tag_filters=tag_filters,
        domain_filters=domain_filters,
        limit=limit,
        db_path=DB_PATH,
    )

    if not active_query and not active_filters:
        st.caption(f"{len(results)}件（初期表示は最大{DEFAULT_PREVIEW_LIMIT}件。検索語か絞り込みで対象を絞れます）")
    else:
        st.caption(f"{len(results)}件（最大{SEARCH_RESULT_LIMIT}件表示）")
    if not results and (active_query or active_filters):
        render_no_search_results(active_query, active_filters)
        return
    render_result_cards(results, key_prefix="search")


def render_no_search_results(active_query: str, active_filters: bool) -> None:
    if active_query and active_filters:
        st.warning(f"「{active_query}」を検索しましたが、現在の絞り込み条件に一致する用語はありません。")
        st.caption("絞り込みを外すか、全文検索・あいまい検索に切り替えると見つかる場合があります。")
    elif active_query:
        st.warning(f"「{active_query}」を検索しましたが、一致する用語は登録されていません。")
        st.caption("表記ゆれがありそうな場合は、全文検索またはあいまい検索も試せます。")
    else:
        st.warning("現在の絞り込み条件に一致する用語はありません。")
        st.caption("神話体系・種別・属性・タグの条件を少し減らすと見つかる場合があります。")


def has_active_filters(
    filters: dict[str, str],
    tag_filters: list[str],
    domain_filters: list[str],
) -> bool:
    return any(value.strip() for value in filters.values()) or bool(tag_filters or domain_filters)


def apply_search_query() -> None:
    st.session_state.applied_search_query = st.session_state.get("search_query", "").strip()
    st.session_state.selected_id = None


def clear_search_query() -> None:
    st.session_state.search_query = ""
    st.session_state.applied_search_query = ""
    st.session_state.selected_id = None
    st.query_params.clear()


def current_query_param(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
    except Exception:
        value = st.experimental_get_query_params().get(name, [""])
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip()


def render_result_cards(entries: list[dict], *, key_prefix: str) -> None:
    if not entries:
        st.info("該当する用語がありません。")
        return

    for entry in entries:
        with st.container(border=True):
            title_col, action_col = st.columns([5, 1])
            with title_col:
                st.subheader(entry["term"])
                english_names = english_aliases(entry)
                if english_names:
                    st.caption(" / ".join(english_names))
                if entry.get("summary"):
                    st.write(entry["summary"])
                metadata = compact_metadata(entry)
                if metadata:
                    st.caption(metadata)
                if "fuzzy_score" in entry:
                    st.caption(f"あいまい一致: {entry['fuzzy_score']:.0f}")
            with action_col:
                if st.button("詳細", key=f"{key_prefix}_open_{entry['id']}", use_container_width=True):
                    st.session_state.selected_id = entry["id"]
                    rerun()


def compact_metadata(entry: dict) -> str:
    parts = []
    for field in ("mythology", "kind", "language", "domains", "tags"):
        value = entry.get(field, "")
        if value:
            parts.append(f"{FIELD_LABELS[field]}: {value}")
    return " / ".join(parts)


def english_aliases(entry: dict) -> list[str]:
    names = []
    term_key = str(entry.get("term", "")).casefold()
    for alias in list_field(entry, "aliases"):
        if alias.casefold() == term_key:
            continue
        if re.search(r"[A-Za-z]", alias):
            names.append(alias)
    return names[:4]


def non_english_aliases(entry: dict) -> list[str]:
    return [alias for alias in list_field(entry, "aliases") if alias not in english_aliases(entry)]


def render_detail(entry_id: int) -> None:
    entry = get_entry(entry_id, DB_PATH)
    if not entry:
        st.warning("選択中の用語が見つかりません。")
        st.session_state.selected_id = None
        return

    st.header(entry["term"])
    english_names = english_aliases(entry)
    if english_names:
        st.caption(" / ".join(english_names))
    if entry.get("reading"):
        st.caption(entry["reading"])
    if entry.get("summary"):
        st.write(entry["summary"])

    meta_cols = st.columns(4)
    for col, field in zip(meta_cols, ("mythology", "kind", "language", "domains")):
        with col:
            st.metric(FIELD_LABELS[field], entry.get(field) or "-")

    if entry.get("tags"):
        st.caption(f"タグ: {entry['tags']}")
    local_aliases = non_english_aliases(entry)
    if local_aliases:
        st.write(f"別名: {', '.join(local_aliases)}")

    if entry.get("description"):
        st.markdown(entry["description"])

    see_also = list_field(entry, "see_also")
    if see_also:
        st.write("関連語")
        cols = st.columns(min(4, len(see_also)))
        for index, related in enumerate(see_also):
            with cols[index % len(cols)]:
                if st.button(related, key=f"see_{entry_id}_{related}", use_container_width=True):
                    jump_to_term(related)

    render_related_suggestions(entry)

    if entry.get("sources"):
        st.write("出典/参考")
        for source in list_field(entry, "sources"):
            st.write(source)

    edit_col, close_col = st.columns([1, 1])
    with edit_col:
        st.caption(f"ID: {entry['id']} / 更新: {entry['updated_at']}")
    with close_col:
        if st.button("詳細を閉じる", use_container_width=True):
            st.session_state.selected_id = None
            rerun()

    with st.expander("編集"):
        render_edit(entry)


def render_related_suggestions(entry: dict) -> None:
    related_entries = find_related_entries(entry["id"], limit=RELATED_RESULT_LIMIT, db_path=DB_PATH)
    if not related_entries:
        return

    with st.expander("近い項目", expanded=False):
        for related in related_entries:
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"**{related['term']}**")
                if related.get("summary"):
                    st.caption(related["summary"])
                if related.get("related_reason"):
                    st.caption(related["related_reason"])
            with cols[1]:
                if st.button("開く", key=f"related_{entry['id']}_{related['id']}", use_container_width=True):
                    st.session_state.selected_id = related["id"]
                    rerun()


def jump_to_term(term: str) -> None:
    entry = get_entry_by_term(term, DB_PATH)
    if entry:
        st.session_state.selected_id = entry["id"]
    else:
        st.session_state.selected_id = None
        st.session_state.search_query = term
    rerun()


def render_add() -> None:
    st.header("追加")
    payload, submitted, duplicate_mode = render_entry_form(
        key_prefix="new",
        submit_label="追加",
        show_duplicate_mode=True,
    )
    if not submitted:
        return

    duplicates = find_entries_by_term(payload["term"], DB_PATH)
    if duplicates and duplicate_mode == "警告して止める":
        st.warning(f"同じ見出し語が{len(duplicates)}件あります。更新または新規作成を選んでください。")
        render_duplicate_list(duplicates)
        return

    if duplicates and duplicate_mode == "既存を更新":
        update_entry(duplicates[0]["id"], payload, DB_PATH)
        st.session_state.selected_id = duplicates[0]["id"]
        st.success("既存の用語を更新しました。")
        return

    new_id = create_entry(payload, DB_PATH)
    st.session_state.selected_id = new_id
    st.success("用語を追加しました。")


def render_duplicate_list(entries: list[dict]) -> None:
    for entry in entries:
        st.caption(f"ID {entry['id']}: {entry.get('summary', '')}")


def render_edit(entry: dict) -> None:
    payload, submitted, _ = render_entry_form(
        initial=entry,
        key_prefix=f"edit_{entry['id']}",
        submit_label="保存",
    )
    if submitted:
        update_entry(entry["id"], payload, DB_PATH)
        st.success("保存しました。")
        rerun()

    st.divider()
    confirm = st.checkbox("この用語を削除する", key=f"delete_confirm_{entry['id']}")
    if st.button("削除", disabled=not confirm, key=f"delete_{entry['id']}"):
        delete_entry(entry["id"], DB_PATH)
        st.session_state.selected_id = None
        st.success("削除しました。")
        rerun()


def render_entry_form(
    *,
    key_prefix: str,
    initial: dict | None = None,
    submit_label: str,
    show_duplicate_mode: bool = False,
) -> tuple[dict, bool, str | None]:
    initial = initial or {}
    duplicate_mode = None
    with st.form(f"{key_prefix}_form"):
        col1, col2 = st.columns(2)
        with col1:
            term = st.text_input(FIELD_LABELS["term"], value=initial.get("term", ""), key=f"{key_prefix}_term")
            reading = st.text_input(
                FIELD_LABELS["reading"], value=initial.get("reading", ""), key=f"{key_prefix}_reading"
            )
            aliases = st.text_input(
                FIELD_LABELS["aliases"], value=initial.get("aliases", ""), key=f"{key_prefix}_aliases"
            )
            language = st.text_input(
                FIELD_LABELS["language"], value=initial.get("language", ""), key=f"{key_prefix}_language"
            )
            kind = st.text_input(FIELD_LABELS["kind"], value=initial.get("kind", ""), key=f"{key_prefix}_kind")
            mythology = st.text_input(
                FIELD_LABELS["mythology"], value=initial.get("mythology", ""), key=f"{key_prefix}_mythology"
            )
        with col2:
            domains = st.text_input(
                FIELD_LABELS["domains"], value=initial.get("domains", ""), key=f"{key_prefix}_domains"
            )
            tags = st.text_input(FIELD_LABELS["tags"], value=initial.get("tags", ""), key=f"{key_prefix}_tags")
            see_also = st.text_input(
                FIELD_LABELS["see_also"], value=initial.get("see_also", ""), key=f"{key_prefix}_see_also"
            )
            sources = st.text_area(
                FIELD_LABELS["sources"], value=initial.get("sources", ""), key=f"{key_prefix}_sources", height=110
            )
            if show_duplicate_mode:
                duplicate_mode = st.radio(
                    "同名がある場合",
                    ["警告して止める", "既存を更新", "新規作成"],
                    horizontal=True,
                    key=f"{key_prefix}_duplicate_mode",
                )

        summary = st.text_area(
            FIELD_LABELS["summary"], value=initial.get("summary", ""), key=f"{key_prefix}_summary", height=90
        )
        description = st.text_area(
            FIELD_LABELS["description"],
            value=initial.get("description", ""),
            key=f"{key_prefix}_description",
            height=260,
        )

        submitted = st.form_submit_button(submit_label)

    payload = {
        "term": term,
        "reading": reading,
        "aliases": aliases,
        "language": language,
        "kind": kind,
        "mythology": mythology,
        "domains": domains,
        "tags": tags,
        "summary": summary,
        "description": description,
        "see_also": see_also,
        "sources": sources,
    }
    if submitted and not term.strip():
        st.error("見出し語は必須です。")
        return payload, False, duplicate_mode
    return payload, submitted, duplicate_mode


def render_reverse_lookup() -> None:
    st.header("逆引き")
    signature = db_signature()
    mythologies = cached_filter_values("mythology", signature)
    kinds = cached_filter_values("kind", signature)
    languages = cached_filter_values("language", signature)
    domains = cached_filter_values("domains", signature)
    tags = cached_filter_values("tags", signature)

    option_query = st.text_input(
        "候補を絞る",
        key="reverse_filter_query",
        placeholder="例: 雷 / 地名 / イスラム",
    ).strip()
    col1, col2, col3 = st.columns(3)
    with col1:
        domain_filters = render_multi_filter(st, "属性/分野", domains, "reverse_domains", option_query)
    with col2:
        tag_filters = render_multi_filter(st, "タグ", tags, "reverse_tags", option_query)
    with col3:
        kind = render_scalar_filter(st, "種別", kinds, "reverse_kind", option_query)

    col4, col5 = st.columns(2)
    with col4:
        mythology = render_scalar_filter(st, "神話体系", mythologies, "reverse_mythology", option_query)
    with col5:
        language = render_scalar_filter(st, "言語", languages, "reverse_language", option_query)

    cols = st.columns([3, 1])
    with cols[0]:
        render_active_filter_summary(st, mythology, kind, language, domain_filters, tag_filters)
    with cols[1]:
        st.button(
            "条件をリセット",
            use_container_width=True,
            on_click=reset_filter_state,
            args=("reverse",),
        )

    results = list_entries(
        filters={"mythology": mythology, "kind": kind, "language": language},
        tag_filters=tag_filters,
        domain_filters=domain_filters,
        limit=REVERSE_RESULT_LIMIT,
        db_path=DB_PATH,
    )
    st.caption(f"{len(results)}件（最大{REVERSE_RESULT_LIMIT}件表示）")
    render_result_cards(results, key_prefix="reverse")


def render_import_export() -> None:
    st.header("Import")
    uploaded = st.file_uploader("CSV / JSON / JSONL", type=["csv", "json", "jsonl"])
    conflict_label = st.radio("重複term", list(CONFLICT_MODES.keys()), horizontal=True)
    if st.button("Import", disabled=uploaded is None):
        try:
            assert uploaded is not None
            rows = parse_uploaded_file(uploaded.name, uploaded.getvalue())
            stats = import_rows(rows, conflict=CONFLICT_MODES[conflict_label], db_path=DB_PATH)
            st.success(
                f"作成 {stats['created']} / 更新 {stats['updated']} / スキップ {stats['skipped']}"
            )
            if stats["errors"]:
                st.error("\n".join(stats["errors"][:10]))
        except Exception as exc:
            st.error(f"Importに失敗しました: {exc}")

    st.divider()
    st.header("Export")
    entries = export_all(DB_PATH)
    st.caption(f"{len(entries)}件")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "CSV",
            data=export_csv(entries).encode("utf-8-sig"),
            file_name="dictionary_export.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "JSON",
            data=export_json(entries).encode("utf-8"),
            file_name="dictionary_export.json",
            mime="application/json",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "Markdown",
            data=export_markdown(entries).encode("utf-8"),
            file_name="dictionary_export.md",
            mime="text/markdown",
            use_container_width=True,
        )


def parse_uploaded_file(name: str, data: bytes) -> list[dict]:
    suffix = Path(name).suffix.lower()
    if suffix == ".csv":
        return parse_csv_bytes(data)
    return parse_json_bytes(data)


def render_manage() -> None:
    st.header("管理")
    st.metric("登録数", count_entries(DB_PATH))
    st.write(f"DB: {DB_PATH}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("サンプルデータを投入", use_container_width=True):
            result = seed_database(db_path=DB_PATH, force=False)
            st.success(
                f"作成 {result['created']} / 更新 {result['updated']} / スキップ {result['skipped']}"
            )
    with col2:
        if st.button("FTSを再構築", use_container_width=True):
            rebuild_fts(DB_PATH)
            st.success("再構築しました。")

    render_quality_panel()


def render_quality_panel() -> None:
    with st.expander("辞書の点検", expanded=False):
        stats = quality_stats(DB_PATH)
        cols = st.columns(4)
        cols[0].metric("短い説明", stats["short_description"])
        cols[1].metric("英語表記なし", stats["missing_english"])
        cols[2].metric("関連語なし", stats["missing_see_also"])
        cols[3].metric("出典なし", stats["missing_sources"])

        issue_labels = {
            "short_description": "短い説明",
            "missing_english": "英語表記なし",
            "missing_see_also": "関連語なし",
            "missing_sources": "出典なし",
        }
        selected_issue = st.selectbox(
            "確認する項目",
            list(issue_labels.keys()),
            format_func=lambda key: issue_labels[key],
            key="quality_issue",
        )
        rows = list_quality_entries(selected_issue, limit=50, db_path=DB_PATH)
        st.caption(f"{len(rows)}件表示（最大50件）")
        for entry in rows:
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f"**{entry['term']}**")
                if entry.get("summary"):
                    st.caption(entry["summary"])
            with cols[1]:
                if st.button("開く", key=f"quality_open_{selected_issue}_{entry['id']}", use_container_width=True):
                    st.session_state.selected_id = entry["id"]
                    st.session_state.active_page = "検索"
                    rerun()


if __name__ == "__main__":
    main()
