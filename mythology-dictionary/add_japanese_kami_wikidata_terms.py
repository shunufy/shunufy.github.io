from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import requests

from db import DB_PATH, get_connection, insert_entry
from models import list_field


OUT_PATH = Path("data/japanese_kami_wikidata_terms.json")
CACHE_PATH = Path("data/wikidata_japanese_kami_cache.json")
BACKUP_PATH = DB_PATH.with_name("dictionary.before_japanese_kami.sqlite3")
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "LocalMythDictionaryBuilder/1.0 (local personal dictionary)"

KAMI_QID = "Q524158"

BLOCK_RE = re.compile(
    r"妖怪|怪談|漫画|アニメ|ゲーム|映画|小説|テレビ|"
    r"fictional character|anime|manga|video game|film|novel",
    re.IGNORECASE,
)

DOMAIN_RULES = [
    ("太陽", r"太陽|sun|solar"),
    ("月", r"月|moon|lunar"),
    ("星", r"星|star|stellar"),
    ("火", r"火|fire|flame"),
    ("水", r"水|water"),
    ("海", r"海|sea|ocean|marine"),
    ("川", r"川|river"),
    ("山", r"山|mountain"),
    ("木", r"木|tree|wood"),
    ("草", r"草|grass|plant"),
    ("石", r"石|rock|stone"),
    ("雷", r"雷|thunder|lightning"),
    ("風", r"風|wind"),
    ("大地", r"土|大地|earth|land"),
    ("食物", r"食|穀|稲|米|food|grain|rice"),
    ("豊穣", r"豊穣|農|fertility|harvest|agriculture"),
    ("知恵", r"知恵|思考|wisdom|knowledge"),
    ("力", r"力|strength|force"),
    ("武", r"武|軍|剣|war|battle|sword"),
    ("鏡", r"鏡|mirror"),
    ("道", r"道|road|path"),
    ("境界", r"境|boundary|crossroad"),
    ("黄泉", r"黄泉|冥|death|underworld"),
    ("家", r"家|宮|house|palace"),
    ("医薬", r"医|薬|medicine|healing"),
]

EN_CONCEPTS = {
    "strength": "力",
    "mirrors": "鏡",
    "mirror": "鏡",
    "wisdom": "知恵",
    "mountain": "山",
    "mountains": "山",
    "water": "水",
    "sea": "海",
    "ocean": "海",
    "food": "食物",
    "grain": "穀物",
    "rice": "稲",
    "agriculture": "農耕",
    "fertility": "豊穣",
    "fire": "火",
    "thunder": "雷",
    "wind": "風",
    "road": "道",
    "roads": "道",
    "medicine": "医薬",
    "healing": "癒し",
    "creation": "創造",
    "underworld": "黄泉",
    "death": "死",
    "war": "武",
    "battle": "武",
    "sword": "剣",
}


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

    query = f"""
    SELECT ?item ?jaLabel ?enLabel ?jaDesc ?enDesc
           (GROUP_CONCAT(DISTINCT ?alias; separator=", ") AS ?aliases)
           (GROUP_CONCAT(DISTINCT ?classLabel; separator=", ") AS ?classLabels)
    WHERE {{
      ?item wdt:P31/wdt:P279* wd:{KAMI_QID} .
      ?item rdfs:label ?jaLabel FILTER(LANG(?jaLabel) = "ja") .
      OPTIONAL {{ ?item rdfs:label ?enLabel FILTER(LANG(?enLabel) = "en") }}
      OPTIONAL {{ ?item schema:description ?jaDesc FILTER(LANG(?jaDesc) = "ja") }}
      OPTIONAL {{ ?item schema:description ?enDesc FILTER(LANG(?enDesc) = "en") }}
      OPTIONAL {{ ?item skos:altLabel ?alias FILTER(LANG(?alias) = "ja") }}
      OPTIONAL {{
        ?item wdt:P31 ?class .
        ?class rdfs:label ?classLabel FILTER(LANG(?classLabel) = "ja")
      }}
    }}
    GROUP BY ?item ?jaLabel ?enLabel ?jaDesc ?enDesc
    ORDER BY ?jaLabel
    LIMIT 1000
    """
    rows = []
    for binding in sparql(query)["results"]["bindings"]:
        rows.append(
            {
                "qid": binding["item"]["value"].rsplit("/", 1)[-1],
                "url": binding["item"]["value"],
                "term": binding["jaLabel"]["value"].strip(),
                "en_label": binding.get("enLabel", {}).get("value", "").strip(),
                "ja_desc": binding.get("jaDesc", {}).get("value", "").strip(),
                "en_desc": binding.get("enDesc", {}).get("value", "").strip(),
                "aliases": binding.get("aliases", {}).get("value", "").strip(),
                "class_labels": binding.get("classLabels", {}).get("value", "").strip(),
            }
        )
    CACHE_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def existing_names() -> set[str]:
    names: set[str] = set()
    with get_connection(DB_PATH) as conn:
        for row in conn.execute("SELECT term, aliases FROM entries").fetchall():
            names.add(row["term"].casefold())
            for alias in list_field(dict(row), "aliases"):
                names.add(alias.casefold())
    return names


def split_aliases(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def infer_domains(text: str) -> str:
    domains = []
    for domain, pattern in DOMAIN_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            domains.append(domain)
    return ", ".join(domains[:5])


def en_concepts(text: str) -> list[str]:
    low = text.lower()
    values = []
    for key, value in EN_CONCEPTS.items():
        if key in low and value not in values:
            values.append(value)
    return values[:4]


def kind_from_classes(classes: str) -> str:
    if "ヒト" in classes or "架空かもしれない人間" in classes or "夫婦" in classes:
        return "神/人物"
    if "山神" in classes or "水神" in classes or "軍神" in classes:
        return "神"
    return "神"


def make_summary(row: dict[str, Any], domains: str, kind: str) -> str:
    desc = row["ja_desc"].strip()
    classes = row["class_labels"].strip()
    en_desc = row["en_desc"].strip()

    if desc and desc not in {"日本神話の神", "日本神話に登場する神", "日本の神", "神道の神"}:
        return ensure_period(desc)

    concepts = en_concepts(en_desc)
    if concepts:
        return f"日本神話・神道に伝わる、{ '・'.join(concepts) }に関わる神格。"

    class_bits = [bit for bit in split_aliases(classes) if bit not in {"神", "ヒト"}]
    if class_bits:
        return f"日本神話・神道に伝わる{class_bits[0]}。"

    if domains:
        return f"日本神話・神道に伝わる、{domains.split(', ')[0]}に関わる神格。"

    if kind == "神/人物":
        return "日本神話・神道に伝わる、神格化された人物または伝説的人物。"
    return "日本神話・神道に伝わる神格。"


def ensure_period(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if text and text[-1] not in "。.!?！？":
        text += "。"
    return text


def is_good_candidate(row: dict[str, Any], names: set[str], selected: set[str]) -> bool:
    term = row["term"].strip()
    if not term or len(term) < 2:
        return False
    text = " ".join([term, row["ja_desc"], row["en_desc"], row["class_labels"], row["aliases"]])
    if BLOCK_RE.search(text):
        return False

    candidate_names = {term.casefold(), row.get("en_label", "").casefold()}
    candidate_names.update(alias.casefold() for alias in split_aliases(row.get("aliases", "")))
    candidate_names.discard("")
    if candidate_names & names or candidate_names & selected:
        return False
    return True


def build_entry(row: dict[str, Any]) -> dict[str, str]:
    text = " ".join([row["term"], row["ja_desc"], row["en_desc"], row["class_labels"]])
    domains = infer_domains(text)
    kind = kind_from_classes(row["class_labels"])
    aliases = split_aliases(row.get("aliases", ""))
    if row.get("en_label"):
        aliases.append(row["en_label"])
    aliases = list(dict.fromkeys(alias for alias in aliases if alias and alias != row["term"]))
    summary = make_summary(row, domains, kind)

    description = [
        summary,
        f"分類：{kind}。由来：日本神話・神道・日本民間信仰。",
    ]
    if row["class_labels"]:
        description.append(f"Wikidata上の分類：{row['class_labels']}。")
    if row["en_desc"]:
        description.append(f"補足（Wikidata英語説明）：{row['en_desc']}。")

    tags = ["Wikidata追加", "八百万の神", "日本神話", "神道"]
    for class_label in split_aliases(row["class_labels"]):
        if class_label not in {"神", "ヒト"}:
            tags.append(class_label)

    return {
        "term": row["term"],
        "reading": "",
        "aliases": ", ".join(aliases),
        "language": "Japanese",
        "kind": kind,
        "mythology": "日本",
        "domains": domains,
        "tags": ", ".join(dict.fromkeys(tags)),
        "summary": summary,
        "description": "\n".join(description),
        "see_also": "",
        "sources": row["url"],
    }


def select_entries() -> list[dict[str, str]]:
    names = existing_names()
    selected_names: set[str] = set()
    candidates = fetch_candidates()
    candidates.sort(
        key=lambda row: (
            row["ja_desc"] in {"", "日本神話の神", "日本神話に登場する神", "日本の神", "神道の神"},
            row["class_labels"] in {"", "神"},
            row["term"],
        )
    )

    entries = []
    for row in candidates:
        if not is_good_candidate(row, names, selected_names):
            continue
        entry = build_entry(row)
        selected_names.add(entry["term"].casefold())
        selected_names.update(alias.casefold() for alias in split_aliases(entry["aliases"]))
        entries.append(entry)
    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def main() -> None:
    entries = select_entries()
    shutil.copy2(DB_PATH, BACKUP_PATH)
    with get_connection(DB_PATH) as conn:
        for entry in entries:
            insert_entry(conn, entry)
    print({"created": len(entries), "backup": str(BACKUP_PATH), "export": str(OUT_PATH)})


if __name__ == "__main__":
    main()
