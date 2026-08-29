#!/usr/bin/env python3
"""One-way migration from insight frontmatter sources to ## 外部ソース."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def migrate(text: str, path: Path) -> tuple[str, int]:
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise ValueError(f"invalid frontmatter: {path}")
    lines = match.group(1).splitlines()
    output: list[str] = []
    sources: list[str] = []
    index = 0
    found = False
    while index < len(lines):
        if lines[index] != "sources:":
            output.append(lines[index])
            index += 1
            continue
        if found:
            raise ValueError(f"duplicate sources key: {path}")
        found = True
        index += 1
        while index < len(lines) and re.match(r"^  - ", lines[index]):
            value = lines[index][4:].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            sources.append(value)
            index += 1
    existing_sections = text.count("## 外部ソース")
    if existing_sections > 1:
        raise ValueError(f"duplicate 外部ソース: {path}")
    if existing_sections == 1 and found:
        raise ValueError(f"both sources and 外部ソース exist: {path}")
    if existing_sections == 1:
        return text, len(re.findall(r"(?m)^- S[1-9][0-9]*（", text))
    if not found:
        raise ValueError(f"sources key missing: {path}")
    retained = [source for source in sources if not source.startswith("topic:")]
    section = ["## 外部ソース", ""]
    if retained:
        for number, source in enumerate(retained, 1):
            section.append(f"- S{number}（要確認）: {source} — 対応する主張を未確認。")
    else:
        section.append("外部ソース未確認。")
    body = match.group(2).rstrip()
    migrated = "---\n" + "\n".join(output) + "\n---\n" + body + "\n\n" + "\n".join(section) + "\n"
    return migrated, len(retained)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pages_dir", type=Path, nargs="?", default=Path("wiki/insight/pages"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pages = sorted(args.pages_dir.glob("*.md"))
    source_count = 0
    results: list[tuple[Path, str]] = []
    for page in pages:
        result, count = migrate(page.read_text(encoding="utf-8"), page)
        results.append((page, result))
        source_count += count
    if not args.check:
        for page, result in results:
            page.write_text(result, encoding="utf-8")
    print(f"MIGRATION_OK pages={len(pages)} external_sources={source_count} mode={'check' if args.check else 'write'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
