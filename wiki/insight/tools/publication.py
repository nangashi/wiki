#!/usr/bin/env python3
"""Determine whether an insight page may be newly published in the index."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from evaluation_state import (current_design_rubric_version, current_rubric_version, git_blob, latest_design_evaluations,
                              latest_evaluations, parse_metadata)
from insight_source_validator import validate

SLUG = r"[a-z0-9][a-z0-9-]*"


def approved_insight(root: Path, slug: str) -> bool:
    pages = root / "wiki" / "insight" / "pages"
    page = pages / f"{slug}.md"
    if not page.is_file() or validate(page):
        return False
    version = current_rubric_version(pages)
    records, _invalid = latest_evaluations(pages, root / "evaluations" / "insight", version)
    current = next((record for record in records if record["slug"] == slug), None)
    if not (current and current.get("status") == "current" and current.get("rubric_version") == version and current.get("pass") is True): return False
    # Index admission always requires the complete design/article pair.
    return bool(current.get("design_state") == "complete" and
                current.get("design_alignment") == "合格")



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    if not re.fullmatch(SLUG, args.slug):
        print(f"ERROR: invalid slug: {args.slug}", file=sys.stderr)
        return 2
    try:
        allowed = approved_insight(args.root.resolve(), args.slug)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(f"INSIGHT_PUBLICATION {'ALLOW' if allowed else 'DENY'} slug={args.slug}")
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
