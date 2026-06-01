from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


CATEGORY_EXTENSIONS = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".tiff"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".ppt", ".pptx"},
    "Archives": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".xml", ".java", ".cs"},
    "Apps": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"},
    "Data": {".csv", ".tsv", ".xlsx", ".xls", ".sqlite", ".db"},
}


@dataclass(frozen=True)
class MovePlan:
    source: Path
    destination: Path


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"


def destination_folder(base: Path, path: Path, strategy: str) -> Path:
    if strategy == "category":
        return base / category_for(path)
    if strategy == "extension":
        suffix = path.suffix.lower().lstrip(".") or "no-extension"
        return base / suffix
    if strategy == "date":
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        return base / f"{modified:%Y-%m}"
    raise ValueError(f"Unknown strategy: {strategy}")


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def iter_files(root: Path, recursive: bool, include_hidden: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    files = []
    for path in root.glob(pattern):
        if not path.is_file():
            continue
        if not include_hidden and any(is_hidden(part) for part in path.relative_to(root).parents):
            continue
        if not include_hidden and is_hidden(path):
            continue
        files.append(path)
    return sorted(files)


def build_plan(root: Path, strategy: str, recursive: bool = False, include_hidden: bool = False) -> list[MovePlan]:
    root = root.expanduser().resolve()
    plans: list[MovePlan] = []
    reserved: set[Path] = set()

    for source in iter_files(root, recursive=recursive, include_hidden=include_hidden):
        target_dir = destination_folder(root, source, strategy)
        if source.parent == target_dir:
            continue
        destination = unique_destination(target_dir / source.name)
        while destination in reserved:
            destination = unique_destination(destination.with_name(f"{destination.stem}-next{destination.suffix}"))
        reserved.add(destination)
        plans.append(MovePlan(source=source, destination=destination))
    return plans


def apply_plan(plans: list[MovePlan]) -> None:
    for plan in plans:
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan.source), str(plan.destination))


def format_plan(root: Path, plans: list[MovePlan]) -> str:
    if not plans:
        return "No files need to be moved."

    lines = ["Planned moves:", ""]
    for index, plan in enumerate(plans, start=1):
        source = plan.source.relative_to(root)
        destination = plan.destination.relative_to(root)
        lines.append(f"{index:>3}. {source} -> {destination}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely organize a Downloads folder.")
    parser.add_argument("folder", type=Path, help="Folder to organize.")
    parser.add_argument(
        "--strategy",
        choices=("category", "extension", "date"),
        default="category",
        help="How destination folders are chosen.",
    )
    parser.add_argument("--apply", action="store_true", help="Move files. Without this, only preview.")
    parser.add_argument("--recursive", action="store_true", help="Scan nested folders too.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and folders.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.folder.expanduser().resolve()

    if not root.exists() or not root.is_dir():
        parser.exit(2, f"error: folder does not exist or is not a directory: {root}\n")

    plans = build_plan(root, strategy=args.strategy, recursive=args.recursive, include_hidden=args.include_hidden)
    print(format_plan(root, plans))

    if args.apply and plans:
        apply_plan(plans)
        print(f"\nMoved {len(plans)} file(s).")
    elif plans:
        print("\nDry run only. Re-run with --apply to move files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

