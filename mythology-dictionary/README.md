# Mythology Dictionary

[![CI](https://github.com/shunufy/shunufy.github.io/actions/workflows/ci.yml/badge.svg)](https://github.com/shunufy/shunufy.github.io/actions/workflows/ci.yml)

A local-first mythology and folklore dictionary built with Streamlit, SQLite,
FTS5, and RapidFuzz.

The project is designed for creators, game developers, writers, and learners
who want a searchable reference for mythological names, deities, legendary
places, artifacts, motifs, and folklore terms.

## Highlights

- 2,000+ bundled entries in `data/dictionary.sqlite3`.
- Quick search, SQLite full-text search, and fuzzy search.
- Filters for mythology, kind, language, domains, and tags.
- Detail pages with aliases, summaries, descriptions, related terms, and source notes.
- CSV, JSON, JSONL, and Markdown import/export.
- Local-only default Streamlit configuration bound to `127.0.0.1`.
- Tests and dictionary integrity checks for ongoing maintenance.

## Quick Start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Or on Windows:

```powershell
start_local.bat
```

Then open:

```text
http://127.0.0.1:8501/
```

## Project Structure

```text
mythology-dictionary/
  app.py                       Streamlit UI
  db.py                        SQLite schema, CRUD, search, quality queries
  models.py                    Entry normalization and list-field helpers
  import_export.py             CSV, JSON, JSONL, and Markdown import/export
  seed.py                      Seed data loader
  data/dictionary.sqlite3      Bundled dictionary database
  data/*.json                  Themed data packs and enrichment batches
  scripts/check_dictionary.py  Database and JSON integrity checks
  tests/test_db.py             Database and search behavior tests
```

## Data Model

| Field | Purpose |
| --- | --- |
| `term` | Main display name. |
| `reading` | Reading, kana, transliteration, or pronunciation hint. |
| `aliases` | Alternate names, English forms, and spelling variants. |
| `language` | Language or broad source language. |
| `kind` | Deity, creature, place, artifact, concept, text, etc. |
| `mythology` | Mythology, folklore, religion, or cultural tradition. |
| `domains` | High-level domains such as sky, sea, death, war, fertility. |
| `tags` | Search-friendly labels. |
| `summary` | One short, useful sentence. |
| `description` | Practical explanation with distinguishing detail. |
| `see_also` | Related entries. |
| `sources` | Stable references or source notes. |

## Maintenance Checks

```powershell
python scripts/check_dictionary.py
python -m pytest tests
python -m compileall app.py db.py models.py import_export.py seed.py scripts tests
```

## Import and Export

The app supports:

- CSV import/export
- JSON import/export
- JSONL import
- Markdown export

Import conflict handling supports skip, overwrite, and alias-merge modes.

## Curation Policy

This project focuses on real mythology, folklore, legendary geography,
religious tradition, named artifacts, and culturally attested motifs. Fictional
or franchise-only material should stay out of scope unless the project scope is
explicitly expanded.

See:

- [Data Sources and Curation Policy](DATA_SOURCES.md)
- [Contributing](CONTRIBUTING.md)
- [Development Log](DEVELOPMENT_LOG.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Quality Summary](reports/quality-summary.md)

## Current Status

This is an early public release of a project that was first developed locally.
The public repository now includes the app, bundled data, tests, reproducible
data packs, maintenance documentation, and CI configuration.

## License

The source code in this directory is released under the MIT License. Dictionary
data is curated for practical reference use; see `DATA_SOURCES.md` for source
and curation notes.
