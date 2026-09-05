#!/usr/bin/env python3
"""Classify insight wiki pages against anki/state.json without modifying either."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def criteria_version(path: Path) -> int:
    match = re.search(r"(?m)^version:\s*(\d+)\s*$", path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"version not found in {path}")
    return int(match.group(1))


def main() -> int:
    default_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    pages_dir = root / "wiki/insight/pages"
    state_path = args.state or root / "anki/state.json"
    criteria_path = root / "anki/card-criteria.md"

    try:
        current_version = criteria_version(criteria_path)
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        state_pages = state.get("pages", {})
        if not isinstance(state_pages, dict):
            raise ValueError("state.pages must be an object")
        state_version = state.get("criteriaVersion")

        current = {path.stem: sha256_file(path) for path in sorted(pages_dir.glob("*.md"))}
        result = {"criteriaVersion": current_version, "new": [], "changed": [], "deleted": [], "unchanged": []}

        for slug, digest in current.items():
            saved = state_pages.get(slug)
            if saved is None:
                result["new"].append(slug)
                continue
            reasons = []
            if saved.get("contentHash") != digest:
                reasons.append("contentHash")
            if state_version != current_version:
                reasons.append("criteriaVersion")
            if reasons:
                result["changed"].append({"slug": slug, "reasons": reasons})
            else:
                result["unchanged"].append(slug)

        result["deleted"] = sorted(set(state_pages) - set(current))
        result["counts"] = {key: len(result[key]) for key in ("new", "changed", "deleted", "unchanged")}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"sync_status.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
