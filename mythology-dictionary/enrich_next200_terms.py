from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from db import DB_PATH, get_connection, update_entry_in_conn
from models import ENTRY_FIELDS, merge_multi_values, parse_multi_value


INPUT_PATH = Path("data/next200_before_enrich.json")
OUT_PATH = Path("data/next200_enriched_terms.json")
BACKUP_PATH = DB_PATH.with_name("dictionary.before_next200_enrichment.sqlite3")
TAG = "次200補筆"
SOURCE_NOTE = "既存データをもとに辞典向けに補筆"


def join_items(value: Any, fallback: str = "未整理") -> str:
    items = parse_multi_value(value)
    return "、".join(items) if items else fallback


def compact(text: Any) -> str:
    return str(text or "").strip()


def ensure_sentence(text: str) -> str:
    text = compact(text)
    if not text:
        return ""
    return text if text.endswith(("。", "！", "？", ".", "!", "?")) else f"{text}。"


def category_note(kind: str, mythology: str) -> str:
    kind_text = kind or ""
    mythology_text = mythology or ""

    if "ソロモン72柱" in mythology_text or "悪魔" in kind_text:
        return (
            "悪魔学・魔術書系の項目として見る場合は、階位、姿、授ける知識、召喚者との関係が読みどころになる。"
            "善悪の単純な記号ではなく、契約、誘惑、知識、危険な助力といった役割を持つ存在として整理すると使いやすい。"
        )
    if any(word in kind_text for word in ("神", "女神", "神格", "男神")):
        return (
            "神格として見る場合は、どの自然現象や社会秩序を司るか、どの祭祀・土地・血縁と結びつくかが重要になる。"
            "同じ神でも地域や文献によって性格が変わることがあるため、権能だけでなく物語上の立ち位置も見ると把握しやすい。"
        )
    if any(word in kind_text for word in ("土地", "地名", "都市", "国", "島", "山", "川", "領域", "地域")):
        return (
            "土地・領域として見る場合は、現実の地理なのか、死後世界・楽園・境界領域のような神話的空間なのかで意味が変わる。"
            "物語では到達困難な場所、試練の舞台、神々や英雄の故郷として機能することが多い。"
        )
    if any(word in kind_text for word in ("建物", "宮殿", "神殿", "塔", "城", "館", "祭壇")):
        return (
            "建造物として見る場合は、誰が住む・祀られる・守る場所なのかを押さえると分かりやすい。"
            "神話では単なる背景ではなく、権威、隔離、聖域、禁忌、試練の入口を示す舞台装置になる。"
        )
    if any(word in kind_text for word in ("武器", "剣", "槍", "弓", "道具", "宝物", "神器", "物品")):
        return (
            "神話的な道具として見る場合は、所有者、由来、発揮する力、失われる場面が意味を作る。"
            "武器や宝物は戦闘力だけでなく、王権、誓約、祝福、呪い、試練の達成を示す印として使われやすい。"
        )
    if any(word in kind_text for word in ("怪物", "獣", "竜", "蛇", "鳥", "巨人", "霊", "妖精", "精霊", "ニンフ")):
        return (
            "怪物・精霊として見る場合は、外見の特徴だけでなく、どの場所に現れ、何を脅かし、誰に退治・交渉されるかが要点になる。"
            "自然への畏怖、境界の危険、英雄譚の試練を形にした存在として読むと輪郭がつかみやすい。"
        )
    if any(word in kind_text for word in ("英雄", "人物", "王", "予言者", "聖人", "祖")):
        return (
            "人物項目として見る場合は、血筋、使命、失敗、誰と対立・協力したかを追うと役割が見える。"
            "英雄や王は、個人の武勇だけでなく、共同体の起源、王権の正当化、禁忌を破った結果を背負うことが多い。"
        )
    if any(word in kind_text for word in ("概念", "運命", "死", "法", "美徳", "罪", "儀礼")):
        return (
            "概念として見る場合は、具体的な人物や場所ではなく、神話世界のルールや価値観を説明する語として働く。"
            "創作設定では、宗教観、禁忌、死生観、社会制度を支える基礎語として扱うと便利である。"
        )
    return (
        "辞典項目としては、名前だけで判断せず、属する神話圏、分類、関連する属性を合わせて見ると理解しやすい。"
        "物語上の役割を一言でつかんでから、関連語や出典へ広げると、設定資料として再利用しやすくなる。"
    )


def make_summary(entry: dict[str, Any]) -> str:
    summary = ensure_sentence(compact(entry.get("summary")))
    if len(summary) >= 38:
        return summary

    term = compact(entry.get("term"))
    mythology = compact(entry.get("mythology")) or "神話・伝承"
    kind = compact(entry.get("kind")) or "用語"
    domains = join_items(entry.get("domains"), "")
    if domains:
        return f"{term}は{mythology}に関わる{kind}で、{domains}といった属性から引ける項目。"
    return f"{term}は{mythology}に関わる{kind}で、神話や伝承の人物・土地・概念を整理するための項目。"


def make_description(entry: dict[str, Any], summary: str) -> str:
    term = compact(entry.get("term"))
    mythology = compact(entry.get("mythology")) or "神話・伝承"
    kind = compact(entry.get("kind")) or "用語"
    aliases = join_items(entry.get("aliases"), "")
    domains = join_items(entry.get("domains"), "")
    tags = join_items(entry.get("tags"), "")
    see_also = join_items(entry.get("see_also"), "")
    old_description = ensure_sentence(compact(entry.get("description")))

    intro = ensure_sentence(summary)
    if old_description and old_description != intro and len(old_description) > len(intro) + 20:
        intro = f"{intro}\n\n既存説明: {old_description}"

    parts = [
        intro,
        (
            f"辞典的には、{term}は「{mythology}」の文脈で「{kind}」として扱うと整理しやすい。"
            "まず神話圏と分類を押さえることで、同名・類似名の項目や後世の創作名と混同しにくくなる。"
        ),
    ]

    if aliases:
        parts.append(
            f"別名・英語表記としては「{aliases}」が参照できる。"
            "検索時はカタカナ表記だけでなく、ラテン文字表記や別綴りも合わせて見ると引き当てやすい。"
        )
    if domains:
        parts.append(
            f"関連する属性は「{domains}」。"
            "逆引きでは、この属性から似た役割の神、土地、怪物、道具を並べて比較できる。"
        )

    parts.append(category_note(kind, mythology))

    if see_also:
        parts.append(
            f"関連語としては「{see_also}」も合わせて見るとよい。"
            "人物関係、同じ神話圏の近い概念、対になる存在をたどる入口になる。"
        )
    elif tags and tags != "未整理":
        parts.append(
            f"既存タグでは「{tags}」に分類されている。"
            "タグを手がかりに近い項目を並べると、単語単体では見えにくい文化圏ごとのまとまりが見えてくる。"
        )

    parts.append(
        "創作や世界観設定で使う場合は、名称をそのまま借りるだけでなく、司る領域、禁忌、象徴物、敵対者、信仰される場所を分けてメモしておくと、後から検索しやすい。"
    )
    return "\n\n".join(part for part in parts if part)


def build_enrichment(entry: dict[str, Any]) -> dict[str, str]:
    summary = make_summary(entry)
    description = make_description(entry, summary)
    return {
        "term": compact(entry.get("term")),
        "reading": compact(entry.get("reading")),
        "aliases": compact(entry.get("aliases")),
        "language": compact(entry.get("language")),
        "kind": compact(entry.get("kind")),
        "mythology": compact(entry.get("mythology")),
        "domains": compact(entry.get("domains")),
        "tags": merge_multi_values(entry.get("tags", ""), TAG),
        "summary": summary,
        "description": description,
        "see_also": compact(entry.get("see_also")),
        "sources": merge_multi_values(entry.get("sources", ""), SOURCE_NOTE),
    }


def merge_entry(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {field: existing.get(field, "") for field in ENTRY_FIELDS}
    for field, value in incoming.items():
        if field not in ENTRY_FIELDS or value == "":
            continue
        if field in {"aliases", "domains", "tags", "see_also", "sources"}:
            merged[field] = merge_multi_values(existing.get(field, ""), value)
        else:
            merged[field] = value
    return merged


def main() -> None:
    rows = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    enrichments = {row["id"]: build_enrichment(row) for row in rows}

    if DB_PATH.exists() and not BACKUP_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
    OUT_PATH.write_text(json.dumps(enrichments, ensure_ascii=False, indent=2), encoding="utf-8")

    updated = 0
    with get_connection(DB_PATH) as conn:
        for entry_id, incoming in enrichments.items():
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
            if row is None:
                raise KeyError(f"Entry id={entry_id} was not found")
            existing = {key: row[key] for key in row.keys()}
            update_entry_in_conn(conn, entry_id, merge_entry(existing, incoming))
            updated += 1

    print(f"updated={updated}")
    print(f"backup={BACKUP_PATH}")
    print(f"wrote={OUT_PATH}")


if __name__ == "__main__":
    main()
