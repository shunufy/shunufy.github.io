# Changelog

This log includes both public releases and the local development history that
led to the first public version. It is intentionally practical: it records
visible maintenance work, data expansion, quality passes, and app fixes.

## 0.1.0 - 2026-06-01

Initial public repository release.

- Published the mythology dictionary as a Streamlit + SQLite open-source app.
- Bundled the current `data/dictionary.sqlite3` database with 2,000+ entries.
- Included curated JSON data packs and import/enrichment helper scripts.
- Added test coverage for database CRUD, search, and filter behavior.
- Added CI readiness, dictionary integrity checks, contribution docs, source
  policy notes, roadmap, and security guidance.

## Local Development History

### 2026-05-27

- Added a mythic weapons data pack.
- Verified the local Streamlit app after the latest data expansion.
- Kept backup databases out of the public publishing path.

### 2026-05-19

- Added broader world mythology gap packs.
- Expanded coverage across multiple traditions and regions.
- Preserved import scripts so future batch additions remain reproducible.

### 2026-05-17

- Added Aztec mythology, Abrahamic/Middle Eastern, and Christian core term packs.
- Added or refined Streamlit local-run configuration.
- Continued description-quality work for entries that were too thin.

### 2026-05-16

- Ran additional enrichment passes for short or unclear entries.
- Improved descriptions toward the project standard: one-line identification
  plus a distinctive role, trait, or use case.

### 2026-05-14

- Added Japanese kami-related data and Goetia term coverage.
- Added famous missing terms and supporting report files.
- Added database tests for CRUD, search, and multi-value filters.

### 2026-05-13

- Built the first local Streamlit + SQLite dictionary app.
- Added search, detail pages, filters, import/export, and local startup docs.
- Imported early seed data and player-dictionary/full-pack JSON sources.

