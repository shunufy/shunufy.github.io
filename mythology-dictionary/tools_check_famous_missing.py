import json
import re
import sqlite3
from pathlib import Path


DB = Path("data/dictionary.sqlite3")


def load_names():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("select term, aliases from entries").fetchall()
    conn.close()

    all_names = []
    for row in rows:
        values = [row["term"] or ""]
        aliases = row["aliases"] or ""
        try:
            parsed = json.loads(aliases)
            if isinstance(parsed, list):
                values.extend(str(item) for item in parsed)
        except Exception:
            values.extend(item.strip() for item in re.split("[,、]", aliases) if item.strip())
        all_names.append({value.casefold() for value in values if value})
    return all_names


CHECKS = {
    "Greek": [
        ["ゼウス", "Zeus"],
        ["ヘーラー", "ヘラ", "Hera"],
        ["アテーナー", "アテナ", "Athena"],
        ["アポローン", "アポロン", "Apollo"],
        ["アルテミス", "Artemis"],
        ["アプロディーテー", "アフロディーテ", "Aphrodite"],
        ["アレース", "アレス", "Ares"],
        ["ヘルメース", "ヘルメス", "Hermes"],
        ["ヘーパイストス", "ヘパイストス", "Hephaestus"],
        ["デーメーテール", "デメテル", "Demeter"],
        ["ハーデース", "ハデス", "Hades"],
        ["ポセイドーン", "ポセイドン", "Poseidon"],
        ["ペルセポネー", "ペルセポネ", "Persephone"],
        ["ディオニューソス", "ディオニュソス", "Dionysus"],
        ["メドゥーサ", "Medusa"],
        ["ミーノータウロス", "ミノタウロス", "Minotaur"],
        ["キマイラ", "Chimera"],
        ["ヒュドラー", "ヒュドラ", "Hydra"],
        ["ケルベロス", "Cerberus"],
        ["ペーガソス", "ペガサス", "Pegasus"],
        ["スフィンクス", "Sphinx"],
        ["セイレーン", "Siren"],
        ["キュクロープス", "サイクロプス", "Cyclops"],
    ],
    "Norse": [
        ["オーディン", "Odin"],
        ["トール", "Thor"],
        ["ロキ", "Loki"],
        ["フレイヤ", "フレイア", "Freyja"],
        ["フレイ", "Freyr"],
        ["テュール", "Tyr"],
        ["ヘル", "Hel"],
        ["フェンリル", "Fenrir"],
        ["ヨルムンガンド", "Jormungandr"],
        ["スルト", "Surtr"],
        ["ヴァルキュリャ", "ワルキューレ", "Valkyrie"],
        ["ヴァルハラ", "Valhalla"],
        ["ミーミル", "Mimir"],
        ["ニーズヘッグ", "Nidhogg"],
        ["ユミル", "Ymir"],
        ["スレイプニル", "Sleipnir"],
    ],
    "Egyptian": [
        ["ラー", "Ra"],
        ["イシス", "Isis"],
        ["オシリス", "Osiris"],
        ["ホルス", "Horus"],
        ["アヌビス", "Anubis"],
        ["セト", "Set"],
        ["トート", "Thoth"],
        ["ハトホル", "Hathor"],
        ["マアト", "Maat", "Ma'at"],
        ["セクメト", "Sekhmet"],
        ["アメン", "Amun"],
    ],
    "Mesopotamian": [
        ["イナンナ", "Inanna"],
        ["イシュタル", "Ishtar"],
        ["エンキ", "Enki"],
        ["エンリル", "Enlil"],
        ["マルドゥク", "Marduk"],
        ["ティアマト", "Tiamat"],
        ["エレシュキガル", "Ereshkigal"],
        ["ネルガル", "Nergal"],
        ["ウトゥ", "Utu"],
        ["ナンナ", "シン", "Nanna", "Sin"],
    ],
    "Indian": [
        ["ブラフマー", "Brahma"],
        ["ヴィシュヌ", "Vishnu"],
        ["シヴァ", "Shiva"],
        ["ラクシュミー", "Lakshmi"],
        ["サラスヴァティー", "Saraswati"],
        ["カーリー", "Kali"],
        ["ガネーシャ", "Ganesha"],
        ["ハヌマーン", "Hanuman"],
        ["インドラ", "Indra"],
        ["アグニ", "Agni"],
        ["ヴァルナ", "Varuna"],
        ["ヤマ", "Yama"],
        ["ガルダ", "Garuda"],
        ["ナーガ", "Naga"],
    ],
    "Celtic": [
        ["ダグザ", "Dagda"],
        ["モリガン", "Morrigan"],
        ["ルー", "Lugh", "Lug"],
        ["クー・フーリン", "クー・フリン", "Cu Chulainn"],
        ["アラウン", "Arawn"],
        ["ケルヌンノス", "Cernunnos"],
        ["ブリギッド", "Brigid"],
        ["ヌアザ", "Nuada"],
        ["マナナン", "Manannan"],
    ],
    "Mesoamerican": [
        ["ケツァルコアトル", "Quetzalcoatl"],
        ["テスカトリポカ", "Tezcatlipoca"],
        ["ウィツィロポチトリ", "Huitzilopochtli"],
        ["トラロック", "Tlaloc"],
        ["ククルカン", "Kukulkan"],
    ],
    "Slavic": [
        ["ペルーン", "Perun"],
        ["ヴェレス", "Veles"],
        ["バーバ・ヤーガ", "Baba Yaga"],
        ["コシチェイ", "Koschei"],
        ["スヴァローグ", "Svarog"],
        ["モコシ", "Mokosh"],
    ],
    "AngelsDemons": [
        ["ルシファー", "Lucifer"],
        ["ミカエル", "Michael"],
        ["ガブリエル", "Gabriel"],
        ["ラファエル", "Raphael"],
        ["ウリエル", "Uriel"],
        ["メタトロン", "Metatron"],
        ["リリス", "Lilith"],
        ["アザゼル", "Azazel"],
        ["サマエル", "Samael"],
        ["レヴィアタン", "Leviathan"],
        ["ベヒモス", "Behemoth"],
    ],
    "Shichifukujin": [
        ["恵比寿", "蛭子", "Ebisu"],
        ["大黒天", "Daikokuten"],
        ["毘沙門天", "Bishamonten"],
        ["弁財天", "弁才天", "Benzaiten"],
        ["福禄寿", "Fukurokuju"],
        ["寿老人", "Jurojin"],
        ["布袋", "Hotei"],
    ],
}


def has_any(all_names, names):
    lowered = {name.casefold() for name in names}
    if any(values & lowered for values in all_names):
        return True
    for name in lowered:
        if len(name) >= 4 and any(
            any(name in value or value in name for value in values if len(value) >= 4)
            for values in all_names
        ):
            return True
    return False


all_names = load_names()
report = []
for group, items in CHECKS.items():
    missing = [item[0] for item in items if not has_any(all_names, item)]
    report.append(
        {"group": group, "present": len(items) - len(missing), "total": len(items), "missing": missing}
    )

Path("data/famous_missing_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
