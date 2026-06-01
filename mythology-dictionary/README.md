# 用語辞典

神話・伝承・世界観設定用語をローカルで管理する SQLite + Streamlit 製の辞典アプリです。
外部APIは使いません。データは `data/dictionary.sqlite3` に保存されます。

## ローカル専用で開く

Windowsでは、まずこれを使ってください。

```powershell
start_local.bat
```

起動後、ブラウザで次を開きます。

```text
http://127.0.0.1:8501/
```

`127.0.0.1` は自分のPCだけを指すローカルアドレスです。インターネット上に公開するURLではありません。

## 初回セットアップ

Python 3.11+ を入れた状態で、このフォルダを PowerShell で開いて実行します。

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
start_local.bat
```

`py` が使えない場合は、代わりに `python` を使ってください。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
start_local.bat
```

## 手動で起動する場合

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

`.streamlit/config.toml` でも `127.0.0.1` 固定にしているため、通常の `streamlit run app.py` でもローカル専用で起動します。

## できること

- 用語の追加・編集・削除
- クイック検索、全文検索、あいまい検索
- 神話体系、種別、言語、属性、タグでの絞り込み
- 属性やタグからの逆引き
- 関連語ジャンプ
- 詳細ページで近い項目を表示
- CSV / JSON / JSONL import
- CSV / JSON / Markdown export
- 管理ページで辞書の点検

## データ項目

| field | 内容 |
| --- | --- |
| term | 見出し語 |
| reading | 読み/かな |
| aliases | 別名・英語表記 |
| language | 言語 |
| kind | 種別 |
| mythology | 神話体系 |
| domains | 属性/分野 |
| tags | タグ |
| summary | 短い説明 |
| description | 詳説 |
| see_also | 関連語 |
| sources | 出典/参考 |

`aliases`, `domains`, `tags`, `see_also`, `sources` はカンマ区切りで複数指定できます。

## テスト

```powershell
python -m pytest
```

## 主なファイル

```text
app.py                 Streamlit UI
db.py                  SQLite初期化、CRUD、検索
models.py              入力整形、複数値の正規化
import_export.py       CSV/JSON/Markdown入出力
seed.py                初期データ投入
start_local.bat        ローカル専用起動
.streamlit/config.toml Streamlitローカル専用設定
data/dictionary.sqlite3 辞書DB
tests/test_db.py       最小テスト
```
