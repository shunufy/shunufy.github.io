# Development Log

This file gives reviewers and contributors a compact view of the project's
maintenance trail before and after the first public release.

## Current Public Baseline

- Public repository path: `mythology-dictionary/`
- App stack: Streamlit, SQLite, FTS5, RapidFuzz
- Current bundled database: `data/dictionary.sqlite3`
- Current entry count: 2,000+
- Validation:
  - `python scripts/check_dictionary.py`
  - `python -m pytest tests`
  - `python -m compileall app.py db.py models.py import_export.py seed.py scripts tests`

## Maintenance Themes

- Expand coverage across mythology and folklore traditions.
- Improve short descriptions and make each entry useful at a glance.
- Add source notes and related terms over time.
- Keep imports reproducible through themed scripts and data packs.
- Preserve local-first behavior so users can run and edit the dictionary safely.

## Pre-Public Work Summary

| Date | Focus | Result |
| --- | --- | --- |
| 2026-05-13 | Local app build | Streamlit + SQLite MVP with search, filters, detail view, import/export, and seed data. |
| 2026-05-14 | Early content expansion | Japanese kami, Goetia, and famous-missing-term coverage plus database tests. |
| 2026-05-16 | Description quality | Enrichment passes for thin entries and clearer at-a-glance summaries. |
| 2026-05-17 | Themed packs | Aztec, Abrahamic/Middle Eastern, and Christian core term packs. |
| 2026-05-19 | World coverage gaps | Broader world mythology gap packs and reproducible import scripts. |
| 2026-05-27 | Mythic weapons | Added mythic weapons pack and verified the local app after expansion. |
| 2026-06-01 | Public release prep | Published repository version with CI, docs, data policy, roadmap, and dictionary checks. |

## Near-Term Maintenance Plan

- Add screenshots and a short demo GIF.
- Create a `v0.1.0` GitHub release after CI passes.
- Add duplicate and source-coverage reports.
- Improve source coverage for the most visible entries.
- Add issues for roadmap items so maintenance work is visible and trackable.

