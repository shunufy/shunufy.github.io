from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from db import DB_PATH, get_connection, update_entry_in_conn
from models import ENTRY_FIELDS, merge_multi_values


INPUT_PATH = Path("data/next100_before_enrich.json")
OUT_PATH = Path("data/next100_enriched_terms.json")
BACKUP_PATH = DB_PATH.with_name("dictionary.before_next100_enrichment.sqlite3")


FACTS: dict[int, dict[str, str]] = {
    1348: {"reading": "あるぷ", "aliases": "Alp", "kind": "怪物/夢魔", "mythology": "ドイツ民間伝承", "domains": "悪夢, 睡眠, 夢魔, 圧迫, 夜", "summary": "ドイツ民間伝承の悪夢をもたらす怪物。眠る人の胸に乗り、息苦しさや金縛りを起こす夢魔として語られる。", "fact": "アルプはドイツ語圏の民間伝承に見られる夜の怪異で、眠っている人を圧迫し悪夢を見せる存在とされる。夢魔・金縛り・睡眠中の恐怖を人格化した存在として理解すると使いやすい。", "see_also": "夢魔, ナイトメア, インキュバス"},
    1590: {"reading": "あるぺいおす", "aliases": "Alpheus, アルフェイオス", "language": "Greek", "kind": "河神", "mythology": "ギリシャ", "domains": "川, 水, 追跡, ニンフ, 地下水", "summary": "ギリシャ神話の河神。ニンフのアレトゥーサを追い、川と泉が地下でつながる物語で知られる。", "fact": "アルペイオスはペロポネソス半島を流れる川を神格化した河神で、アレトゥーサへの恋と追跡の物語が有名である。水脈が地上と地下、ギリシャとシチリアをつなぐという神話的想像を担う。", "see_also": "アレトゥーサ, 河神, オーケアノス"},
    881: {"reading": "あるます", "aliases": "Almace, Almice, アルマーチェ", "kind": "伝説武器/剣", "mythology": "シャルルマーニュ伝説", "domains": "剣, 聖職者, 騎士道, 聖戦, 叙事詩", "summary": "シャルルマーニュ伝説で大司教テュルパンの剣とされる名剣。聖職者と騎士道が重なる武器名。", "fact": "アルマスは中世フランスの武勲詩・シャルルマーニュ伝説に関わる剣で、しばしば大司教テュルパンの武器とされる。聖職者が戦場に立つという中世叙事詩的な緊張を帯びている。", "see_also": "デュランダル, テュルパン, シャルルマーニュ"},
    1310: {"reading": "あるやさあ", "aliases": "Al-Yasa, Elisha in Islam, エリシャ", "language": "Arabic", "kind": "預言者", "mythology": "イスラーム/アブラハム系", "domains": "預言, 継承, 奇跡, 教え, 信仰", "summary": "イスラームで預言者の一人とされる人物。聖書のエリシャに対応し、預言の継承を象徴する。", "fact": "アルヤサアはクルアーンに名が挙がる預言者で、聖書伝承のエリシャに対応するとされる。師から受け継いだ預言の力、信仰の継承、共同体を導く役割に焦点を置くと分かりやすい。", "see_also": "エリヤ, 預言者, イスラーム"},
    1440: {"reading": "ある・うっざー", "aliases": "Al-Uzza, Al-‘Uzzá, アルウッザー", "language": "Arabic", "kind": "女神", "mythology": "アラビア", "domains": "力, 星, 戦, 聖域, 女神", "summary": "イスラーム以前のアラビアで崇拝された有力な女神。名は力強さを連想させ、聖域や保護と結びつく。", "fact": "アル・ウッザーはイスラーム以前のアラビアで崇拝された女神で、アッラート、マナートとともに三女神として語られることがある。戦いや星、聖域の守護と結びつけられ、砂漠都市の古い信仰を象徴する。", "see_also": "アッラート, マナート, アラビア神話"},
    98: {"reading": "あれす", "aliases": "Ares, Mars, アレース", "language": "Greek", "kind": "戦神", "mythology": "ギリシャ", "domains": "戦争, 暴力, 血, 破壊, 勇猛", "summary": "ギリシャ神話の戦神。戦略よりも戦場の暴力、血の熱、荒々しい衝突を象徴する。", "fact": "アレスはオリュンポス十二神の一柱で、戦争の中でも血気、混乱、殺傷、衝動的な暴力を強く表す。知略の戦いを担うアテナと対比すると性格が分かりやすい。", "see_also": "アレース, アテナ, マルス"},
    1441: {"reading": "あれとぅーさ", "aliases": "Arethusa", "language": "Greek", "kind": "ニンフ/泉", "mythology": "ギリシャ", "domains": "泉, 川, 逃走, 変身, 水", "summary": "ギリシャ神話の水のニンフ。河神アルペイオスから逃れ、泉へ姿を変えた物語で知られる。", "fact": "アレトゥーサはアルテミスに仕えるニンフで、河神アルペイオスの追跡から逃れるため泉へ変じたとされる。水が逃避、変身、地中を通るつながりを表す物語である。", "see_also": "アルペイオス, アルテミス, ニンフ"},
    1115: {"reading": "あれーす", "aliases": "Ares, アレス", "language": "Greek", "kind": "戦神", "mythology": "ギリシャ", "domains": "戦争, 暴力, 血, 恐怖, 争い", "summary": "アレスの長音表記。ギリシャ神話で戦場の荒々しさと暴力を司る神。", "fact": "アレースはアレスの別表記で、戦争の血なまぐさい側面を神格化した存在である。英雄的な規律より、衝動、怒号、恐怖、破壊を背負う神として描くと個性が出る。", "see_also": "アレス, アテナ, 戦争"},
    1520: {"reading": "あろける", "aliases": "Allocer, Alloces, Alocer", "language": "Latin, English", "kind": "悪魔/魔神", "mythology": "悪魔学/ソロモン72柱", "domains": "天文学, 学芸, 騎士, 炎, 知識", "summary": "ソロモン72柱の第52柱。獅子顔の騎士の姿で現れ、天文学と自由学芸を教える公爵。", "fact": "アロケルは Ars Goetia の第52柱で、公爵位の悪魔である。燃える目を持つ獅子の顔の兵士が馬に乗る姿で語られ、学問を授けるが威圧感の強い武装教師のような性格を持つ。", "see_also": "ソロモン72柱, 天文学, 悪魔"},
    919: {"reading": "あろん", "aliases": "Aaron, Harun, ハールーン", "language": "Hebrew, Arabic", "kind": "祭司/聖書人物", "mythology": "ヘブライ聖書/イスラーム", "domains": "祭司, 兄弟, 杖, 出エジプト, 儀礼", "summary": "モーセの兄で、イスラエル最初の祭司長とされる人物。祭司職と儀礼の始まりを象徴する。", "fact": "アロンはモーセの兄として出エジプトの物語に登場し、語り手・補佐役・祭司長として重要な役割を担う。アロンの杖、祭司の衣、幕屋祭儀など、神との契約を儀礼として保つ側面を象徴する。", "see_also": "モーセ, 出エジプト, 祭司"},
    870: {"reading": "あろんだいと", "aliases": "Arondight, Aroundight", "language": "Middle English", "kind": "伝説武器/剣", "mythology": "アーサー王伝説", "domains": "剣, 騎士, ランスロット, 名誉, 決闘", "summary": "アーサー王伝説でランスロットの剣とされる名剣。騎士の武勇と名誉を帯びた武器名。", "fact": "アロンダイトは中世騎士道物語でランスロットの剣とされることが多い名である。エクスカリバーほど王権の象徴ではなく、最強の騎士個人の武勇、愛、罪、名誉の複雑さを帯びる剣として扱える。", "see_also": "ランスロット, エクスカリバー, アーサー王"},
    854: {"reading": "あんか", "aliases": "Anqa, Anka, アンカー", "language": "Arabic", "kind": "霊鳥/怪鳥", "mythology": "アラビア", "domains": "鳥, 不死鳥, 砂漠, 予兆, 長寿", "summary": "アラビア伝承に見える巨大な霊鳥。フェニックスに似た幻鳥として語られることがある。", "fact": "アンカはアラビア伝承の巨大な雌鳥で、人面や長い首、多数の翼を持つと説明されることがある。フェニックスやシームルグのような霊鳥伝承と響き合い、砂漠の彼方に現れる稀な鳥として使いやすい。", "see_also": "フェニックス, シームルグ, 霊鳥"},
    986: {"reading": "あんがだ", "aliases": "Angada", "language": "Sanskrit", "kind": "英雄/王子", "mythology": "インド", "domains": "猿族, 王子, 使者, ラーマーヤナ, 王権", "summary": "『ラーマーヤナ』に登場する猿族の王子。ヴァーリの子で、ラーマ側の勇士・使者として活躍する。", "fact": "アンガダはインド叙事詩『ラーマーヤナ』の人物で、猿王ヴァーリとターラーの子である。ラーマ陣営で戦い、ラーヴァナへの使者としても語られるため、若い王子、忠誠、父の因縁を背負う戦士として扱いやすい。", "see_also": "ラーマ, ハヌマーン, ラーマーヤナ"},
    1442: {"reading": "あんげろす", "aliases": "Angelos", "language": "Greek", "kind": "女神/神格", "mythology": "ギリシャ", "domains": "冥界, ヘカテ, 浄化, 逃走, 女神", "summary": "ギリシャ神話でゼウスとヘラの娘とされる神格。冥界やヘカテとの関係で語られる。", "fact": "アンゲロスはゼウスとヘラの娘とされるマイナーな神格で、物語によっては盗みや逃走、冥界での浄化を経てヘカテと結びつけられる。大きな主神ではないが、境界を越えて性格を変える神として面白い。", "see_also": "ヘカテ, ヘラ, ゼウス"},
    1591: {"reading": "あんしゃる", "aliases": "Anshar, Anšar", "language": "Akkadian", "kind": "原初神", "mythology": "メソポタミア", "domains": "天空, 原初, 創世, 神々の祖, 宇宙", "summary": "バビロニア創世神話の原初神。キシャルと対になり、神々の祖として宇宙生成の初期に置かれる。", "fact": "アンシャルは『エヌマ・エリシュ』に登場する原初神で、キシャルと対になる存在である。名は天の全体を思わせ、アヌなど後続の神々へつながる系譜上の祖として重要である。", "see_also": "キシャル, アヌ, エヌマ・エリシュ"},
    908: {"reading": "あんだか", "aliases": "Andhaka", "language": "Sanskrit", "kind": "アスラ/怪物", "mythology": "インド", "domains": "盲目, 欲望, シヴァ, 血, 戦い", "summary": "インド神話のアスラ。盲目や欲望の象徴として語られ、シヴァとの戦いで知られる。", "fact": "アンダカはインド神話に登場するアスラで、シヴァとパールヴァティーに関わる複雑な出生や、パールヴァティーへの欲望からシヴァと戦う物語で知られる。血から増殖する怪物的な側面もあり、制御不能な欲望を象徴する。", "see_also": "シヴァ, パールヴァティー, アスラ"},
}


def base_note(entry: dict[str, Any]) -> str:
    term = entry["term"]
    myth = entry.get("mythology") or "伝承"
    kind = entry.get("kind") or "用語"
    summary = entry.get("summary") or f"{myth}に関わる{kind}。"
    aliases = entry.get("aliases") or ""
    domains = entry.get("domains") or ""
    alias_note = f"別表記として「{aliases}」も参照される。" if aliases else "表記ゆれや別名が伝承・作品ごとに生じやすい。"
    domain_note = f"連想しやすい領域は「{domains}」。" if domains else "関連する属性は、由来する神話体系や物語上の役割から整理すると掴みやすい。"
    if "汎用" in myth or "固有名" in kind:
        role = "実在神話の中心的な固有名というより、既存神話の語感やモチーフを借りた創作用語として扱うと安全である。"
    elif "悪魔" in kind or "ソロモン72柱" in myth:
        role = "悪魔学の文脈では、姿・階位・授ける能力・もたらす危険を分けて見ると辞典項目として使いやすい。"
    elif any(word in kind for word in ("神", "女神", "神格")):
        role = "神格として見る場合、司る領域だけでなく、どの共同体・土地・儀礼で重要だったかを押さえると名前の使いどころがはっきりする。"
    elif any(word in kind for word in ("地名", "異界", "都市")):
        role = "神話地理として見る場合、そこが楽園・冥界・聖地・失われた土地のどれに近いかで印象が大きく変わる。"
    elif any(word in kind for word in ("人物", "英雄", "預言者", "王")):
        role = "人物項目としては、血筋・使命・失敗・誰との関係で語られるかを見ると物語上の役割が分かりやすい。"
    elif any(word in kind for word in ("物品", "武器", "剣", "弓")):
        role = "神話物品としては、単なる道具ではなく、誰が持ち、何を正当化し、どんな試練や権威と結びつくかが重要になる。"
    else:
        role = "伝承上の位置づけ、象徴、関連する物語を合わせて見ると、単なる名前以上の使い方が見えてくる。"
    return f"{summary}\n\n辞典的には、{term}は「{myth}」の中で{kind}として扱うと整理しやすい。{alias_note}{domain_note}{role}世界観設定では、由来を示す固有名、関連勢力の象徴、土地・儀式・武器・人物名の参照元として使える。"


def build_enrichment(entry: dict[str, Any]) -> dict[str, str]:
    fact = FACTS.get(entry["id"], {})
    summary = fact.get("summary") or entry.get("summary") or f"{entry['term']}に関する伝承用語。"
    description_fact = fact.get("fact")
    if description_fact:
        description = (
            f"{description_fact}\n\n"
            f"辞典的には、由来・象徴・物語上の役割を分けて見ると使いやすい。"
            f"既存の分類では「{fact.get('mythology') or entry.get('mythology', '')}」の"
            f"「{fact.get('kind') or entry.get('kind', '')}」として整理でき、"
            f"関連する属性は「{fact.get('domains') or entry.get('domains', '')}」。"
            f"世界観設定では、名前の響きだけでなく、背後にある神話的役割を反映させることで、"
            f"人物・土地・神器・勢力名として自然に使える。"
        )
    else:
        description = base_note(entry)

    return {
        "term": fact.get("term", entry.get("term", "")),
        "reading": fact.get("reading", entry.get("reading", "")),
        "aliases": merge_multi_values(entry.get("aliases", ""), fact.get("aliases", "")),
        "language": fact.get("language", entry.get("language", "")),
        "kind": fact.get("kind", entry.get("kind", "")),
        "mythology": fact.get("mythology", entry.get("mythology", "")),
        "domains": merge_multi_values(entry.get("domains", ""), fact.get("domains", "")),
        "tags": merge_multi_values(entry.get("tags", ""), fact.get("tags", ""), "次100補筆"),
        "summary": summary,
        "description": description,
        "see_also": merge_multi_values(entry.get("see_also", ""), fact.get("see_also", "")),
        "sources": merge_multi_values(entry.get("sources", ""), "既存データをもとに辞典向けに補筆"),
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
