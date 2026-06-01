from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from db import DB_PATH, get_connection, insert_entry


TARGET_COUNT = 1000
OUT_PATH = Path("data/non_japanese_wikidata_terms_1000.json")
CACHE_PATH = Path("data/wikidata_candidate_cache_v2.json")
BACKUP_PATH = DB_PATH.with_name("dictionary.before_wikidata_1000.sqlite3")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "LocalMythDictionaryBuilder/1.0 (local personal dictionary)"


@dataclass(frozen=True)
class Root:
    qid: str
    kind: str
    tag: str


ROOTS = [
    Root("Q178885", "神", "神格"),
    Root("Q205985", "神", "女神"),
    Root("Q482380", "神", "神"),
    Root("Q2239243", "怪物/伝承存在", "怪物"),
    Root("Q193291", "精霊/存在", "精霊"),
    Root("Q177413", "悪魔/魔物", "悪魔"),
    Root("Q235113", "天使/霊的存在", "天使"),
    Root("Q13002315", "英雄/人物", "伝説的人物"),
    Root("Q12334344", "英雄/人物", "英雄"),
    Root("Q6949213", "王/人物", "神話王"),
    Root("Q3238337", "地名/異界", "神話地理"),
    Root("Q20203727", "神話物品", "神器/物品"),
]

JAPAN_BLOCK_RE = re.compile(
    r"日本|神道|神社|天津神|国津神|現御神|権現|八百万|"
    r"千葉県|下総国|上総|武蔵|大和|尾張|越後|出羽|信濃|常陸|"
    r"江戸|明治|平安|鎌倉|京都|大阪|東京|妖怪|"
    r"北海道|東北地方|関東|中部地方|近畿|中国地方|四国|九州|沖縄|"
    r"青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|埼玉|"
    r"新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|"
    r"滋賀|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|"
    r"徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|佐渡|"
    r"Shinto|Japanese|Japan|kami|Ainu|Ryukyuan|琉球|アイヌ|妖怪ウォッチ",
    re.IGNORECASE,
)

MEDIA_BLOCK_RE = re.compile(
    r"曖昧さ回避|ウィキメディア|一覧|カテゴリ|"
    r"fictional character|Marvel|DC Comics|Dungeons & Dragons|Pok[eé]mon|"
    r"Final Fantasy|Warhammer|The Elder Scrolls|video game|anime|manga|"
    r"television|film|novel|comic|role-playing game|board game|"
    r"Cthulhu|Lovecraft|Pastafarian|Flying Spaghetti|"
    r"hypothetical|theoretical|"
    r"架空の|漫画|アニメ|ゲーム|映画|小説|テレビ|"
    r"クトゥルフ|ラヴクラフト|パロディ|空飛ぶスパゲッティ|セレマ|UFO|仮想|提唱",
    re.IGNORECASE,
)

MYTHOLOGY_RULES = [
    ("ギリシャ", r"ギリシ|Greek|Hellenic"),
    ("ローマ", r"ローマ|Roman"),
    ("北欧", r"北欧|Norse|Scandinavian|Germanic"),
    ("エジプト", r"エジプト|Egyptian"),
    ("メソポタミア", r"メソポタミア|Sumerian|Akkadian|Babylonian|Assyrian|Mesopotamian"),
    ("インド", r"インド|ヒンドゥ|Hindu|Indian|Sanskrit|Vedic"),
    ("ジャイナ/インド", r"ジャイナ|Jain"),
    ("仏教", r"仏教|Buddhist"),
    ("中国", r"中国|Chinese|Taoist|Daoist"),
    ("ケルト", r"ケルト|Celtic|Irish|Welsh|Gaelic|Breton"),
    ("アーサー", r"アーサー|Arthurian"),
    ("スラヴ", r"スラ[ヴブ]|Slavic"),
    ("ヨルバ", r"ヨルバ|Yoruba|orisha"),
    ("アブラハム系", r"キリスト|ユダヤ|イスラム|Christian|Jewish|Islamic|Abrahamic|angel|demon"),
    ("中南米", r"アステカ|マヤ|インカ|Aztec|Maya|Inca|Mesoamerican"),
    ("ポリネシア", r"ポリネシア|Hawaiian|Māori|Maori|Polynesian"),
    ("ゾロアスター/イラン", r"ゾロアスター|ペルシア|イラン|Zoroastrian|Persian|Iranian"),
    ("バルト/フィン", r"バルト|フィン|Finnish|Baltic|Uralic"),
    ("朝鮮", r"朝鮮|韓国|Korean"),
    ("フィリピン", r"フィリピン|Philippine"),
    ("北米先住民", r"Native American|First Nations|Inuit|Ojibwe|Lakota|Navajo"),
    ("エトルリア", r"エトルリア|Etruscan"),
    ("アフリカ", r"African|Zulu|Bantu|Akan|Dahomey|Fon"),
]

DOMAIN_RULES = [
    ("水", r"水|water"),
    ("太陽", r"太陽|sun|solar"),
    ("月", r"月|moon|lunar"),
    ("海", r"海|sea|ocean|marine"),
    ("川", r"川|river"),
    ("火", r"火|fire|flame"),
    ("雷", r"雷|thunder|lightning|storm"),
    ("風", r"風|wind"),
    ("大地", r"大地|earth|land"),
    ("冥界", r"冥界|underworld|dead|death|hell"),
    ("死", r"死|death"),
    ("戦争", r"戦争|war|battle"),
    ("愛", r"愛|love"),
    ("豊穣", r"豊穣|fertility|harvest|agriculture"),
    ("知恵", r"知恵|wisdom|knowledge"),
    ("魔術", r"魔術|magic|witch|sorcery"),
    ("狩猟", r"狩猟|hunt"),
    ("王権", r"王|king|queen|royal"),
    ("創造", r"創造|creator|creation"),
    ("運命", r"運命|fate|destiny"),
    ("山", r"山|mountain"),
    ("空", r"空|sky|heaven"),
    ("蛇", r"蛇|serpent|snake"),
    ("竜", r"竜|龍|dragon"),
]


def sparql(query: str) -> dict[str, Any]:
    response = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def fetch_candidates() -> list[dict[str, Any]]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    all_rows: list[dict[str, Any]] = []
    for root in ROOTS:
        query = f"""
        SELECT ?item ?jaLabel ?enLabel ?jaDesc ?enDesc
               (GROUP_CONCAT(DISTINCT ?classLabel; separator=", ") AS ?classLabels)
               (GROUP_CONCAT(DISTINCT ?contextLabel; separator=", ") AS ?contextLabels)
        WHERE {{
          ?item wdt:P31/wdt:P279* wd:{root.qid} .
          ?item rdfs:label ?jaLabel FILTER(LANG(?jaLabel) = "ja") .
          ?item schema:description ?jaDesc FILTER(LANG(?jaDesc) = "ja") .
          OPTIONAL {{ ?item rdfs:label ?enLabel FILTER(LANG(?enLabel) = "en") }}
          OPTIONAL {{ ?item schema:description ?enDesc FILTER(LANG(?enDesc) = "en") }}
          OPTIONAL {{
            ?item wdt:P31 ?class .
            ?class rdfs:label ?classLabel FILTER(LANG(?classLabel) = "en")
          }}
          OPTIONAL {{
            ?item ?contextProp ?context .
            VALUES ?contextProp {{ wdt:P140 wdt:P172 wdt:P2596 wdt:P361 wdt:P495 }}
            ?context rdfs:label ?contextLabel FILTER(LANG(?contextLabel) = "en")
          }}
        }}
        GROUP BY ?item ?jaLabel ?enLabel ?jaDesc ?enDesc
        ORDER BY ?jaLabel
        LIMIT 1800
        """
        data = sparql(query)
        bindings = data["results"]["bindings"]
        for binding in bindings:
            row = {
                "qid": binding["item"]["value"].rsplit("/", 1)[-1],
                "url": binding["item"]["value"],
                "term": binding["jaLabel"]["value"].strip(),
                "en_label": binding.get("enLabel", {}).get("value", "").strip(),
                "ja_desc": binding["jaDesc"]["value"].strip(),
                "en_desc": binding.get("enDesc", {}).get("value", "").strip(),
                "class_labels": binding.get("classLabels", {}).get("value", "").strip(),
                "context_labels": binding.get("contextLabels", {}).get("value", "").strip(),
                "root_qid": root.qid,
                "root_kind": root.kind,
                "root_tag": root.tag,
            }
            all_rows.append(row)
        time.sleep(0.5)

    CACHE_PATH.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return all_rows


def existing_terms() -> set[str]:
    with get_connection(DB_PATH) as conn:
        rows = conn.execute("SELECT term FROM entries").fetchall()
    return {row["term"].casefold() for row in rows}


def infer_mythology(text: str) -> str:
    for name, pattern in MYTHOLOGY_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return "世界神話/伝承"


def infer_kind(row: dict[str, Any], text: str) -> str:
    desc = row["ja_desc"]
    classes = row.get("class_labels", "")
    if "女神" in desc:
        return "神"
    if "神" in desc and not any(word in desc for word in ("神話", "神殿", "神学")):
        return "神"
    if re.search(r"場所|地名|都市|島|山|川|世界|冥界|天国|地獄|宮殿|王国|国", desc):
        return "地名/異界"
    if re.search(r"武器|剣|槍|盾|指輪|杯|物品|道具|神器|宝", desc):
        return "神話物品"
    if re.search(r"英雄|王|王女|王子|人物|預言者|聖人|騎士", desc):
        return "英雄/人物"
    if re.search(r"怪物|巨人|竜|龍|獣|魔物|悪魔|精霊|妖精|生物|creature|monster", text, re.IGNORECASE):
        return "怪物/伝承存在"
    if "deity" in classes.lower() or row["root_kind"] == "神":
        return "神"
    return row["root_kind"]


def infer_domains(text: str) -> str:
    domains: list[str] = []
    for domain, pattern in DOMAIN_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            domains.append(domain)
    return ", ".join(domains[:5])


def normalize_summary(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if text and text[-1] not in "。.!?！？":
        text += "。"
    return text


def make_summary(row: dict[str, Any], mythology: str, kind: str, domains: str) -> str:
    original = normalize_summary(row["ja_desc"])
    if len(original) >= 12:
        return original

    english_summary = summary_from_english(row.get("en_desc", ""), mythology, kind)
    if english_summary:
        return english_summary

    domain_values = [value.strip() for value in domains.split(",") if value.strip()]
    domain_phrase = ""
    if domain_values:
        domain_phrase = "・".join(domain_values[:3]) + "に関わる"

    if kind == "神":
        return f"{mythology}に伝わる{domain_phrase}神格。"
    if "怪物" in kind or "存在" in kind or "精霊" in kind:
        return f"{mythology}に伝わる{domain_phrase}伝承上の存在。"
    if "地名" in kind:
        return f"{mythology}に伝わる神話上の場所・異界。"
    if "物品" in kind:
        return f"{mythology}に伝わる神話上の道具・宝物。"
    if "人物" in kind or "英雄" in kind or "王" in kind:
        return f"{mythology}に伝わる伝説上の人物。"
    return f"{mythology}に伝わる{domain_phrase}{kind}。"


def summary_from_english(en_desc: str, mythology: str, kind: str) -> str:
    text = en_desc.strip()
    low = text.lower()
    if not text:
        return ""

    concept_map = {
        "childbirth": "出産",
        "midwifery": "助産",
        "discord": "不和",
        "mischief": "災い",
        "deceit": "欺瞞",
        "victory": "勝利",
        "force": "力",
        "affection": "愛情",
        "friendship": "友情",
        "sex": "性愛",
        "forest": "森",
        "plains": "平原",
        "fields": "野",
        "future": "未来",
        "arts": "芸術",
        "music": "音楽",
        "dance": "舞踊",
        "adulthood": "成人",
        "adolescence": "青年期",
        "old age": "老い",
        "sleep": "眠り",
        "dreams": "夢",
        "doom": "破滅",
        "morning star": "明けの明星",
        "evening": "宵の明星",
        "memory": "記憶",
        "envy": "嫉妬",
        "quarrel": "争い",
        "war": "戦争",
    }

    def translate_concepts(fragment: str) -> str:
        found: list[str] = []
        frag = fragment.lower()
        for key, value in concept_map.items():
            if key in frag and value not in found:
                found.append(value)
        return "・".join(found[:4]) or fragment.strip()

    goddess_match = re.search(r"goddess of ([^.;]+)", low)
    if goddess_match:
        return f"{mythology}に伝わる{translate_concepts(goddess_match.group(1))}の女神。"
    god_match = re.search(r"god of ([^.;]+)", low)
    if god_match:
        return f"{mythology}に伝わる{translate_concepts(god_match.group(1))}の神。"
    personification_match = re.search(r"personification of ([^.;]+)", low)
    if personification_match:
        return f"{mythology}に伝わる{translate_concepts(personification_match.group(1))}を擬人化した存在。"
    if "bodhisattva" in low:
        return f"{mythology}に伝わる菩薩。"
    if "nymph" in low and "nurse of zeus" in low:
        return "ギリシャ神話のニンフで、ゼウスの養育者として語られる存在。"
    if "nymph" in low:
        return f"{mythology}に伝わる自然や水辺に関わるニンフ。"
    if "one of the graces" in low:
        return "ギリシャ神話の優雅・美・魅力を司るカリスの一柱。"
    if "horae" in low:
        return "ギリシャ神話の季節や時の秩序に関わるホーライの一柱。"
    if "titan" in low:
        return "ギリシャ神話の古い神族ティタンに属する神格。"
    if "aztec deity" in low or "aztec god" in low:
        return "アステカ神話に伝わる神格。"
    if "egyptian deity" in low or "egyptian goddess" in low:
        return "エジプト神話に伝わる神格。"
    if "norse goddess" in low or "norse god" in low:
        return "北欧神話に伝わる神格。"
    if "roman goddess" in low or "roman god" in low:
        return "ローマ神話に伝わる神格。"
    if "deity in korean folklore" in low:
        return "朝鮮民間伝承に伝わる神格。"
    if "deity" in low and kind == "神":
        return f"{mythology}に伝わる神格。"
    return ""


def is_good_candidate(row: dict[str, Any], existing: set[str], selected: set[str]) -> bool:
    term = row["term"].strip()
    if not term or len(term) < 2:
        return False
    if re.search(r"[ぁ-ん]", term):
        return False
    key = term.casefold()
    if key in existing or key in selected:
        return False
    text = " ".join(
        [
            term,
            row.get("en_label", ""),
            row.get("ja_desc", ""),
            row.get("en_desc", ""),
            row.get("class_labels", ""),
            row.get("context_labels", ""),
        ]
    )
    if JAPAN_BLOCK_RE.search(text):
        return False
    if MEDIA_BLOCK_RE.search(text):
        return False
    if len(row.get("ja_desc", "").strip()) < 3:
        return False
    if re.fullmatch(r"[A-Za-z0-9_ -]+", term) and not row.get("ja_desc"):
        return False
    return True


def build_entry(row: dict[str, Any]) -> dict[str, str]:
    text = " ".join(
        [row["ja_desc"], row.get("en_desc", ""), row.get("class_labels", ""), row.get("context_labels", "")]
    )
    mythology = infer_mythology(text)
    kind = infer_kind(row, text)
    domains = infer_domains(text)
    aliases = row.get("en_label", "")
    tags = ", ".join(
        value
        for value in ["Wikidata追加", "実在神話", "非日本", row["root_tag"], mythology]
        if value
    )
    summary = make_summary(row, mythology, kind, domains)
    description_parts = [
        summary,
        f"分類：{kind}。由来：{mythology}。",
    ]
    if row.get("en_label"):
        description_parts.append(f"英語名/別表記：{row['en_label']}。")
    if domains:
        description_parts.append(f"連想しやすい属性：{domains}。")
    if row.get("en_desc"):
        description_parts.append(f"補足（Wikidata英語説明）：{row['en_desc']}。")
    return {
        "term": row["term"],
        "reading": "",
        "aliases": aliases,
        "language": "",
        "kind": kind,
        "mythology": mythology,
        "domains": domains,
        "tags": tags,
        "summary": summary,
        "description": "\n".join(description_parts),
        "see_also": "",
        "sources": row["url"],
    }


def select_entries() -> list[dict[str, str]]:
    candidates = fetch_candidates()
    existing = existing_terms()
    selected_keys: set[str] = set()
    entries: list[dict[str, str]] = []

    # Prefer named mythological places and objects, then entities whose description is usually concrete.
    root_priority = {root.qid: index for index, root in enumerate(ROOTS)}
    candidates.sort(
        key=lambda row: (
            len(row.get("ja_desc", "")) < 12,
            -len(row.get("ja_desc", "")),
            root_priority.get(row["root_qid"], 999),
            row["term"],
        )
    )

    for row in candidates:
        if not is_good_candidate(row, existing, selected_keys):
            continue
        entry = build_entry(row)
        selected_keys.add(entry["term"].casefold())
        entries.append(entry)
        if len(entries) >= TARGET_COUNT:
            break

    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def main() -> None:
    entries = select_entries()
    if len(entries) < TARGET_COUNT:
        raise RuntimeError(f"Only selected {len(entries)} entries; target was {TARGET_COUNT}")

    shutil.copy2(DB_PATH, BACKUP_PATH)
    with get_connection(DB_PATH) as conn:
        for entry in entries:
            insert_entry(conn, entry)

    print({"created": len(entries), "backup": str(BACKUP_PATH), "export": str(OUT_PATH)})


if __name__ == "__main__":
    main()
