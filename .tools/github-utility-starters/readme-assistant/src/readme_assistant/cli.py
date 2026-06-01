from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class ProjectInfo:
    name: str = "Untitled Project"
    description: str = "A short description of the project."
    features: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=lambda: ["Python 3.10+"])
    installation: str = "python -m pip install -e ."
    usage: str = "python -m package_name --help"
    examples: list[str] = field(default_factory=list)
    configuration: str = ""
    testing: str = "python -m unittest discover -s tests"
    roadmap: list[str] = field(default_factory=list)
    license: str = "MIT"


def normalize_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def load_project_info(path: Path) -> ProjectInfo:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Project metadata must be a JSON object.")

    info = ProjectInfo()
    for key in (
        "name",
        "description",
        "installation",
        "usage",
        "configuration",
        "testing",
        "license",
    ):
        if key in data and data[key] is not None:
            setattr(info, key, str(data[key]).strip())

    for key in ("features", "requirements", "examples", "roadmap"):
        if key in data:
            setattr(info, key, normalize_list(data[key]))
    return info


def merge_cli_args(info: ProjectInfo, args: argparse.Namespace) -> ProjectInfo:
    for key in ("name", "description", "installation", "usage", "configuration", "testing", "license"):
        value = getattr(args, key)
        if value:
            setattr(info, key, value)

    if args.feature:
        info.features = args.feature
    if args.requirement:
        info.requirements = args.requirement
    if args.example:
        info.examples = args.example
    if args.roadmap:
        info.roadmap = args.roadmap
    return info


def prompt_missing(info: ProjectInfo) -> ProjectInfo:
    prompts = {
        "name": "Project name",
        "description": "Short description",
        "installation": "Install command",
        "usage": "Usage command",
    }
    for attr, label in prompts.items():
        current = getattr(info, attr)
        suffix = f" [{current}]" if current else ""
        answer = input(f"{label}{suffix}: ").strip()
        if answer:
            setattr(info, attr, answer)
    return info


def render_list(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def render_code_block(command: str) -> str:
    return f"```bash\n{command.strip()}\n```"


def render_readme(info: ProjectInfo) -> str:
    sections = [
        f"# {info.name}",
        info.description,
        "## Features",
        render_list(info.features, "Add your first feature here."),
        "## Requirements",
        render_list(info.requirements, "Python 3.10+"),
        "## Installation",
        render_code_block(info.installation),
        "## Usage",
        render_code_block(info.usage),
    ]

    if info.examples:
        sections.extend(["## Examples", "\n\n".join(render_code_block(example) for example in info.examples)])
    if info.configuration:
        sections.extend(["## Configuration", info.configuration])

    sections.extend(
        [
            "## Testing",
            render_code_block(info.testing),
        ]
    )

    if info.roadmap:
        sections.extend(["## Roadmap", render_list(info.roadmap, "Add roadmap items.")])

    sections.extend(["## License", info.license])
    return "\n\n".join(section.strip() for section in sections if section.strip()) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a clean README.md for a small project.")
    parser.add_argument("--from-file", type=Path, help="Load project metadata from a JSON file.")
    parser.add_argument("--output", type=Path, default=Path("README.generated.md"), help="Output README path.")
    parser.add_argument("--dry-run", action="store_true", help="Print the README instead of writing it.")
    parser.add_argument("--interactive", action="store_true", help="Prompt for core fields.")
    parser.add_argument("--name")
    parser.add_argument("--description")
    parser.add_argument("--feature", action="append", help="Add a feature bullet. Can be repeated.")
    parser.add_argument("--requirement", action="append", help="Add a requirement bullet. Can be repeated.")
    parser.add_argument("--installation")
    parser.add_argument("--usage")
    parser.add_argument("--example", action="append", help="Add an example command. Can be repeated.")
    parser.add_argument("--configuration")
    parser.add_argument("--testing")
    parser.add_argument("--roadmap", action="append", help="Add a roadmap item. Can be repeated.")
    parser.add_argument("--license")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        info = load_project_info(args.from_file) if args.from_file else ProjectInfo()
        info = merge_cli_args(info, args)
        if args.interactive:
            info = prompt_missing(info)
        output = render_readme(info)
        if args.dry_run:
            sys.stdout.write(output)
            return 0

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote {args.output}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

