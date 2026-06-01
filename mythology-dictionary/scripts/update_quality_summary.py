from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import DB_PATH, quality_stats  # noqa: E402


REPORT_PATH = ROOT / "reports" / "quality-summary.md"


def render_report() -> str:
    stats = quality_stats(DB_PATH)
    return f"""# Quality Summary

Generated for the first public release baseline.

## Snapshot

| Metric | Count |
| --- | ---: |
| Total entries | {stats["total"]:,} |
| Entries with short descriptions | {stats["short_description"]:,} |
| Entries missing English aliases | {stats["missing_english"]:,} |
| Entries missing related terms | {stats["missing_see_also"]:,} |
| Entries missing source notes | {stats["missing_sources"]:,} |

## Interpretation

- Entry descriptions meet the current minimum length check.
- Source fields are populated, but many still need stronger bibliographic detail.
- Related-term coverage is the largest visible data-quality gap.
- English alias coverage needs targeted cleanup for discoverability.

## Next Actions

- Add an automated related-term suggestion report.
- Review high-value entries that lack English aliases.
- Split source quality into stronger categories, such as public-domain text,
  encyclopedia, Wikidata-derived, and manual note.
- Keep this summary updated before tagged releases.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update or verify the quality summary report.")
    parser.add_argument("--check", action="store_true", help="Fail if the checked-in report is stale.")
    args = parser.parse_args(argv)

    expected = render_report()
    if args.check:
        actual = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else ""
        if actual != expected:
            print(f"{REPORT_PATH} is stale. Run scripts/update_quality_summary.py.", file=sys.stderr)
            return 1
        print(f"{REPORT_PATH} is up to date.")
        return 0

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

