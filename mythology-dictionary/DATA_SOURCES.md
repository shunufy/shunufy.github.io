# Data Sources and Curation Policy

This project is a curated local dictionary for mythology, folklore, legendary
objects, and worldbuilding reference terms.

## Current Data Shape

- The bundled SQLite database contains 2,000+ entries.
- Additional JSON packs under `data/` preserve themed import and enrichment
  batches.
- The `sources` field is part of the data model and should be improved over
  time.

## Curation Principles

- Prefer real mythology, folklore, religious tradition, legendary geography,
  texts, named artifacts, and culturally attested motifs.
- Avoid franchise-only terms unless they are clearly separated from real
  mythology and the project scope explicitly expands.
- Every important entry should eventually have a clear source note.
- When source certainty is weak, say so instead of overstating confidence.

## Known Limitations

- Some entries were added through batch imports and still need source cleanup.
- Some descriptions are intentionally short and should be deepened over time.
- The project is not a substitute for academic citation; it is a practical
  reference and search tool.

## Maintenance Targets

- Improve source coverage.
- Merge duplicates and spelling variants.
- Add more non-European traditions with care and source notes.
- Keep import scripts reproducible.

