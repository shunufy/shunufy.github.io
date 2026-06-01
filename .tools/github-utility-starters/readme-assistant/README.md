# README Assistant

Generate a practical `README.md` from command-line flags or a JSON metadata
file. It is intentionally small, dependency-free, and friendly to quick GitHub
publishing.

## Features

- Builds a polished Markdown README with common project sections.
- Accepts repeated `--feature` and `--example` flags.
- Can load project metadata from JSON.
- Supports interactive prompting for missing values.
- Supports `--dry-run` preview before writing.

## Installation

```powershell
python -m pip install -e .
```

## Usage

```powershell
readme-assistant --name "Downloads Organizer" --description "A safe CLI for sorting files." --feature "Dry-run by default" --usage "downloads-organizer ~/Downloads --apply"
```

Preview instead of writing:

```powershell
readme-assistant --from-file examples/project.json --dry-run
```

Write to a custom path:

```powershell
readme-assistant --from-file examples/project.json --output docs/README.generated.md
```

## JSON Input

```json
{
  "name": "Example Tool",
  "description": "A useful command-line helper.",
  "features": ["No dependencies", "Fast setup"],
  "installation": "python -m pip install -e .",
  "usage": "example-tool --help",
  "examples": ["example-tool input.txt --output result.txt"],
  "testing": "python -m unittest discover -s tests",
  "license": "MIT"
}
```

## Development

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## License

MIT

