# shunufy.github.io

[![CI](https://github.com/shunufy/shunufy.github.io/actions/workflows/ci.yml/badge.svg)](https://github.com/shunufy/shunufy.github.io/actions/workflows/ci.yml)

This repository hosts Shunufy's GitHub Pages site and a small collection of
open-source tools.

## Featured Project

### Mythology Dictionary

`mythology-dictionary/` is a local-first Streamlit + SQLite dictionary for
mythology, folklore, legendary objects, and worldbuilding reference terms.

- 2,000+ dictionary entries in the bundled SQLite database.
- Quick, full-text, and fuzzy search modes.
- Filters for mythology, kind, language, domains, and tags.
- CSV, JSON, JSONL, and Markdown import/export support.
- Local-only by default with `127.0.0.1` Streamlit settings.
- Tests and dictionary integrity checks suitable for continuous maintenance.

Start here: [mythology-dictionary/README.md](mythology-dictionary/README.md)

## Utility Starters

`.tools/github-utility-starters/` contains two compact Python CLI starter
projects:

- `readme-assistant`: generate a practical README from CLI flags or JSON.
- `downloads-organizer-cli`: preview and organize a Downloads folder safely.

## Maintenance

```powershell
python -m pip install -r mythology-dictionary/requirements.txt
python mythology-dictionary/scripts/check_dictionary.py
python -m pytest mythology-dictionary/tests
```

The Pages site intentionally asks search engines not to index the public HTML
pages. The OSS project files remain visible in the GitHub repository.
