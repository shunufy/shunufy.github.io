from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from db import DB_PATH, find_related_entries, get_connection, update_entry_in_conn
from models import ENTRY_FIELDS, merge_multi_values, parse_multi_value


OUT_PATH = Path("data/minor_deepening_200.json")
BACKUP_PATH = DB_PATH.with_name("dictionary.before_minor_deepening_200.sqlite3")
TAG = "マイナー深掘り"
SOURCE_NOTE = "既存データをもとにマイナー項目を深掘り補筆"


MAJOR_TERMS = {
    "アキレウス",
    "アフロディーテ",
    "アポロン",
    "アマテラス",
    "アメノウズメ",
    "アレス",
    "アルテミス",
    "イザナギ",
    "イザナミ",
    "エデン",
    "オーディン",
    "ガブリエル",
    "サタン",
    "スサノオ",
    "ゼウス",
    "ツクヨミ",
    "トール",
    "ハデス",
    "ヘカテ",
    "ヘクトール",
    "ヘパイストス",
    "ヘラクレス",
    "ヘラ",
    "ヘルメス",
    "ポセイドン",
    "ミカエル",
    "メフィストフェレス",
    "ラファエル",
    "ルシファー",
    "レヴィアタン",
    "ロキ",
    "地獄",
}

MINOR_KIND_WORDS = {
    "悪魔",
    "怪物",
    "伝承存在",
    "精霊",
    "妖精",
    "ニンフ",
    "小神",
    "地方神",
    "巨人",
    "蛇",
    "竜",
    "鳥",
    "獣",
    "土地",
    "地名",
    "領域",
    "異界",
    "建物",
    "塔",
    "宮殿",
    "武器",
    "道具",
    "概念",
}

GENERIC_MARKERS = (
    "辞典的には",
    "創作や世界観設定",
    "既存説明",
    "物語上の役割",
    "タグを手がかりに",
)


def compact(value: Any) -> str:
    return str(value or "").strip()


def items(value: Any) -> list[str]:
    return parse_multi_value(value)


def join(value: Any, fallback: str = "") -> str:
    values = items(value)
    return "、".join(values) if values else fallback


def one_line(text: str) -> str:
    text = re.sub(r"\s+", " ", compact(text))
    return text


def first_meaningful_sentence(entry: dict[str, Any]) -> str:
    summary = compact(entry.get("summary"))
    if summary:
        return summary if summary.endswith("。") else f"{summary}。"

    description = compact(entry.get("description"))
    for sentence in re.split(r"(?<=。)", description):
        sentence = sentence.strip()
        if sentence:
            return sentence
    return f"{entry['term']}に関する神話・伝承上の用語。"


def candidate_score(entry: dict[str, Any]) -> int:
    term = compact(entry.get("term"))
    if term in MAJOR_TERMS:
        return -100
    if "名称素材" in compact(entry.get("tags")):
        return -100

    kind = compact(entry.get("kind"))
    myth = compact(entry.get("mythology"))
    desc = compact(entry.get("description"))
    see_also = items(entry.get("see_also"))
    aliases = items(entry.get("aliases"))
    domains = items(entry.get("domains"))

    score = 0
    if any(word in kind for word in MINOR_KIND_WORDS):
        score += 8
    if any(marker in desc for marker in GENERIC_MARKERS):
        score += 7
    if not see_also:
        score += 4
    if aliases:
        score += 2
    if domains:
        score += 2
    if myth and myth not in {"ギリシャ", "北欧", "日本"}:
        score += 3
    if "ソロモン72柱" in myth or "悪魔学" in myth:
        score += 4
    if len(desc) < 750:
        score += 3
    if len(desc) > 1300:
        score -= 4
    return score


def pick_candidates(rows: list[dict[str, Any]], limit: int = 200) -> list[dict[str, Any]]:
    if OUT_PATH.exists():
        existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        selected_ids = [int(entry_id) for entry_id in existing.keys()]
        by_id = {row["id"]: row for row in rows}
        fixed = [by_id[entry_id] for entry_id in selected_ids if entry_id in by_id]
        if fixed:
            return fixed[:limit]

    scored = [(candidate_score(row), row) for row in rows]
    scored = [(score, row) for score, row in scored if score > 0]
    scored.sort(
        key=lambda pair: (
            -pair[0],
            compact(pair[1].get("mythology")),
            compact(pair[1].get("kind")),
            compact(pair[1].get("term")),
        )
    )
    return [row for _, row in scored[:limit]]


def kind_focus(kind: str, mythology: str) -> str:
    if "ソロモン72柱" in mythology or "悪魔" in kind:
        return (
            "この種の項目では、単に「悪魔」とだけ覚えるより、階位、現れる姿、授ける知識、危険な助力の種類を分けて見るとよい。"
            "ソロモン伝承や悪魔学では、恐怖の対象であると同時に、知識・技能・予言・誘惑を運ぶ存在として整理される。"
        )
    if any(word in kind for word in ("怪物", "伝承存在", "蛇", "竜", "鳥", "獣")):
        return (
            "怪物・伝承存在としては、外見よりも「どこに現れるか」「何を脅かすか」「誰と対になるか」が重要である。"
            "英雄譚では試練の相手になり、土地伝承では禁忌や自然への畏怖を形にした存在として働く。"
        )
    if any(word in kind for word in ("精霊", "妖精", "ニンフ")):
        return (
            "精霊・妖精系の項目では、支配する自然物や棲む場所がそのまま性格になる。"
            "泉、森、風、山、海などと結びつく場合、個体名というよりも土地の気配や境界の人格化として読むと分かりやすい。"
        )
    if any(word in kind for word in ("土地", "地名", "領域", "異界", "山", "川", "島")):
        return (
            "土地・異界としては、現実の地名なのか、死後世界・楽園・禁域・境界領域なのかを分けると理解しやすい。"
            "物語では移動の目的地であるだけでなく、試練、追放、浄化、再生の舞台として機能することが多い。"
        )
    if any(word in kind for word in ("建物", "塔", "宮殿", "神殿", "館")):
        return (
            "建造物としては、誰が住むか、何を守るか、どんな儀礼や禁忌が結びつくかを見るとよい。"
            "神話では背景ではなく、権威、隔離、聖域、異界への入口を示す装置として使われる。"
        )
    if any(word in kind for word in ("武器", "道具", "宝物", "神器", "アイテム")):
        return (
            "道具・宝物としては、所有者と由来が意味を決める。"
            "単なる強い装備ではなく、王権、誓約、祝福、呪い、失われた正統性を示す印として見ると辞書項目として使いやすい。"
        )
    if any(word in kind for word in ("小神", "地方神", "神", "女神", "男神")):
        return (
            "神格としては、主神かどうかよりも、どの場所・儀礼・自然現象を担当するかが読みどころになる。"
            "小さな神や地方神ほど、特定の土地、職能、季節、生活習慣と強く結びついていることが多い。"
        )
    if "概念" in kind:
        return (
            "概念項目としては、人物名ではなく神話世界のルールや価値観を説明する語として読むとよい。"
            "死生観、罪、浄化、運命、秩序、禁忌を支える語は、世界観設定の基礎語として役立つ。"
        )
    return (
        "この項目は、名前だけでは役割が見えにくいため、神話圏・種別・属性を合わせて読むのが有効である。"
        "関連する土地、人物、象徴を結びつけると、単なる固有名詞ではなく物語上の機能が見えてくる。"
    )


def mythology_focus(mythology: str) -> str:
    if "アブラハム" in mythology or "悪魔学" in mythology:
        return "アブラハム系・悪魔学の語彙では、後世の神学、魔術書、民間伝承が混ざりやすいため、出典層を意識して読むと混同を避けやすい。"
    if "ギリシャ" in mythology:
        return "ギリシャ系では、同じ存在でも叙事詩、悲劇、地方信仰で性格が変わることがあるため、物語ごとの役割を見ると理解が深まる。"
    if "北欧" in mythology:
        return "北欧系では、地名・巨人・道具が宇宙構造や終末観と結びつきやすく、ラグナロクや九つの世界との距離を意識すると把握しやすい。"
    if "エジプト" in mythology:
        return "エジプト系では、地方神、太陽信仰、冥界観、王権儀礼が重なりやすく、神格の姿や動物象徴も重要な手がかりになる。"
    if "ケルト" in mythology or "アーサー" in mythology:
        return "ケルト・アーサー系では、地名、島、宝物、妖精的な存在が英雄の旅や王権の正統性と結びつくことが多い。"
    if "インド" in mythology:
        return "インド系では、神、アスラ、英雄、聖仙が叙事詩やプラーナ文献の中で複数の役割を持つため、血縁と宿命を見ると整理しやすい。"
    if "メソポタミア" in mythology:
        return "メソポタミア系では、都市神、冥界、王権、洪水神話が絡みやすく、神々の系譜や都市との結びつきが重要になる。"
    return "神話圏ごとの文脈を押さえると、同じ「神」「怪物」「土地」でも役割の違いが見えやすくなる。"


def build_related(entry_id: int, existing: Any) -> str:
    current = items(existing)
    if current:
        return ", ".join(current)
    related = find_related_entries(entry_id, limit=4, db_path=DB_PATH)
    names = [row["term"] for row in related if row.get("term")]
    return ", ".join(names[:3])


def build_description(entry: dict[str, Any]) -> str:
    term = compact(entry.get("term"))
    mythology = compact(entry.get("mythology")) or "神話・伝承"
    kind = compact(entry.get("kind")) or "用語"
    domains = join(entry.get("domains"), "未整理")
    aliases = join(entry.get("aliases"), "")
    tags = join(entry.get("tags"), "")
    base = first_meaningful_sentence(entry)

    paragraphs = [
        base,
        (
            f"{term}は、{mythology}の中で「{kind}」として扱うと輪郭をつかみやすい項目である。"
            f"関連する属性は「{domains}」。この属性を手がかりにすると、同じ神話圏の近い存在や、別文化で似た役割を持つ語と比較しやすい。"
        ),
        kind_focus(kind, mythology),
        mythology_focus(mythology),
        (
            "マイナー項目として重要なのは、名前の知名度ではなく、神話世界のどの隙間を埋めているかである。"
            f"{term}の場合は、主神や中心英雄のように物語全体を動かす存在というより、特定の場面、場所、職能、恐れ、儀礼を説明する補助線として読むと使いやすい。"
            "こうした項目を拾っておくと、辞書全体が有名語だけの一覧ではなく、世界の厚みを引ける資料になる。"
        ),
        (
            "見分ける時は、まず同じ神話圏の主要語と並べ、次に種別が近い項目と比べるとよい。"
            "たとえば同じ怪物でも、英雄の敵なのか、土地に棲む災厄なのか、神の眷属なのかで役割は変わる。"
            "同じ地名でも、実在地、冥界、楽園、禁域では物語上の重みが異なる。"
        ),
    ]

    if aliases:
        paragraphs.append(
            f"別名・英語表記としては「{aliases}」が使われる。"
            "表記ゆれで検索できない場合があるため、カタカナ名だけでなく英字名や別綴りも見出しの手がかりになる。"
        )
    if tags:
        paragraphs.append(
            f"既存分類では「{tags}」にも紐づく。"
            "このタグは、あとで同種の小項目をまとめて探すための索引として使える。"
        )

    related_names = [row["term"] for row in find_related_entries(int(entry["id"]), limit=5, db_path=DB_PATH)]
    if related_names:
        paragraphs.append(
            f"近い項目としては「{'、'.join(related_names[:5])}」がある。"
            "これらを一緒に開くと、同じ属性を共有する語、同じ文化圏に属する語、似た役割を持つ語の違いを確認できる。"
            "関連語が完全に一致しなくても、属性や神話圏が重なる項目は逆引きの入口として役に立つ。"
        )

    paragraphs.append(
        f"辞書としては、{term}を「何者か」だけで終わらせず、登場する場面、象徴するもの、似た項目との差を一緒に見ると役に立つ。"
        "世界観設定に使う場合は、役割、出現場所、関係する人物、禁忌や弱点を分けてメモしておくと、後から検索しやすい。"
    )
    return "\n\n".join(one_line(p) for p in paragraphs if compact(p))


def build_summary(entry: dict[str, Any]) -> str:
    summary = compact(entry.get("summary"))
    if len(summary) >= 45:
        return summary
    term = compact(entry.get("term"))
    mythology = compact(entry.get("mythology")) or "神話・伝承"
    kind = compact(entry.get("kind")) or "用語"
    domains = join(entry.get("domains"), "")
    if domains:
        return f"{term}は{mythology}に関わる{kind}で、{domains}を手がかりに引けるマイナー項目。"
    return f"{term}は{mythology}に関わる{kind}で、主要項目の周辺を補うマイナー項目。"


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
    with get_connection(DB_PATH) as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM entries").fetchall()]

    selected = pick_candidates(rows, limit=200)
    enrichments: dict[int, dict[str, str]] = {}
    for row in selected:
        enrichments[row["id"]] = {
            "term": compact(row.get("term")),
            "reading": compact(row.get("reading")),
            "aliases": compact(row.get("aliases")),
            "language": compact(row.get("language")),
            "kind": compact(row.get("kind")),
            "mythology": compact(row.get("mythology")),
            "domains": compact(row.get("domains")),
            "tags": merge_multi_values(row.get("tags", ""), TAG),
            "summary": build_summary(row),
            "description": build_description(row),
            "see_also": build_related(row["id"], row.get("see_also")),
            "sources": merge_multi_values(row.get("sources", ""), SOURCE_NOTE),
        }

    if DB_PATH.exists() and not BACKUP_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)

    OUT_PATH.write_text(
        json.dumps(
            {
                entry_id: {
                    "before": next(row for row in selected if row["id"] == entry_id),
                    "after": data,
                    "score": candidate_score(next(row for row in selected if row["id"] == entry_id)),
                }
                for entry_id, data in enrichments.items()
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

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
    print("first_terms=" + ", ".join(row["term"] for row in selected[:10]))


if __name__ == "__main__":
    main()
