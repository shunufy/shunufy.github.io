# Downloads Organizer CLI

A safe, dependency-free command-line tool for cleaning a Downloads folder. It
previews every move by default and only changes files when `--apply` is passed.

## Features

- Dry-run by default.
- Organizes by category, extension, or date.
- Avoids overwrites by adding numeric suffixes.
- Can skip or include hidden files.
- Handles recursive scans when requested.
- Produces a compact move plan before applying changes.

## Installation

```powershell
python -m pip install -e .
```

## Usage

Preview category-based organization:

```powershell
downloads-organizer "C:\Users\You\Downloads"
```

Apply the changes:

```powershell
downloads-organizer "C:\Users\You\Downloads" --apply
```

Organize by extension:

```powershell
downloads-organizer "C:\Users\You\Downloads" --strategy extension --apply
```

Organize by modified month:

```powershell
downloads-organizer "C:\Users\You\Downloads" --strategy date --apply
```

## Safety Notes

- The tool never moves directories.
- Existing files are not overwritten.
- Without `--apply`, it only prints the planned moves.
- Use `--recursive` carefully; it can move files out of nested folders.

## Development

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## License

MIT

