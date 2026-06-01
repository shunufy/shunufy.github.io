# Contributing

Thank you for helping improve the mythology dictionary.

## Good Entry Standard

Each entry should make the term understandable at a glance:

- Identify what the term is.
- Name the tradition, region, or text family when known.
- Include one distinctive role, trait, story function, or creative use case.
- Add aliases and spelling variants when helpful.
- Add sources when possible, especially for less common entries.

## Preferred Fields

| Field | Guidance |
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

## Local Checks

```powershell
python -m pip install -r requirements.txt
python scripts/check_dictionary.py
python -m pytest tests
```

## Data Hygiene

- Do not commit backup databases such as `dictionary.before_*.sqlite3`.
- Do not commit cache files, logs, `__pycache__`, or `.pytest_cache`.
- Keep generated/import helper scripts focused and reproducible.
- Prefer real mythology and folklore over fictional franchise-only material.

