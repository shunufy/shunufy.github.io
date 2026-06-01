# GitHub Utility Starters

Two small Python CLI projects that are easy to publish, demo, and extend.

## Projects

| Project | Purpose | Safety |
| --- | --- | --- |
| `readme-assistant` | Generate a clean `README.md` from CLI flags or a JSON file. | Writes only to the selected output file. |
| `downloads-organizer-cli` | Preview and organize a Downloads folder by category, extension, or date. | Dry-run by default; requires `--apply` to move files. |

## Quick Start

```powershell
cd readme-assistant
python -m readme_assistant --name "My Tool" --description "A useful CLI." --feature "Fast setup" --usage "my-tool --help" --dry-run
```

```powershell
cd downloads-organizer-cli
python -m downloads_organizer "C:\Users\You\Downloads"
python -m downloads_organizer "C:\Users\You\Downloads" --apply
```

## Repository Layout

```text
github-utility-starters/
  readme-assistant/
  downloads-organizer-cli/
```

Each project has its own `pyproject.toml`, tests, and README so either one can
be split into a separate repository later.

## Validation

```powershell
cd readme-assistant
$env:PYTHONPATH = "src"
python -m unittest discover -s tests

cd ..\downloads-organizer-cli
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

