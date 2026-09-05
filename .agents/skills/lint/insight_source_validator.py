#!/usr/bin/env python3
"""Structural validation for the canonical insight external-source section."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ENTRY = re.compile(r"^- S([1-9][0-9]*)（(一次|二次|参考|要確認)）: (\S.*?) — (\S.*)$")


@dataclass(frozen=True)
class SourceDiagnostic:
    code: str
    category: str
    severity: str
    reason: str


def diagnostic(code: str, reason: str) -> SourceDiagnostic:
    if code in {"SOURCE_MISSING", "SOURCE_UNVERIFIED"}:
        return SourceDiagnostic(code, "quality", "REQUIRED", reason)
    return SourceDiagnostic(code, "structure", "ERROR", reason)


def validate(path: Path) -> list[SourceDiagnostic]:
    text = path.read_text(encoding="utf-8")
    errors: list[SourceDiagnostic] = []
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not frontmatter:
        return [diagnostic("SOURCE_ENTRY_INVALID", "frontmatter_invalid")]
    if re.search(r"(?m)^(?:source|sources)\s*:", frontmatter.group(1)):
        errors.append(diagnostic("SOURCE_ENTRY_INVALID", "frontmatter_source_key_forbidden"))
    headings = list(re.finditer(r"(?m)^## 外部ソース\s*$", text))
    if len(headings) != 1:
        return errors + [diagnostic("SOURCE_MISSING" if not headings else "SOURCE_ENTRY_INVALID", f"section_count={len(headings)}")]
    heading = headings[0]
    later_h2 = re.search(r"(?m)^## ", text[heading.end():])
    if later_h2:
        errors.append(diagnostic("SOURCE_ENTRY_INVALID", "section_not_last"))
    section = text[heading.end():].strip()
    before = text[:heading.start()]
    if "topic:" in section:
        errors.append(diagnostic("SOURCE_ENTRY_INVALID", "topic_marker_forbidden"))
    if section == "外部ソース未確認。":
        errors.append(diagnostic("SOURCE_MISSING", "no_external_source"))
        return errors
    ids: list[str] = []
    kinds: list[str] = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = ENTRY.fullmatch(line)
        if not match:
            errors.append(diagnostic("SOURCE_ENTRY_INVALID", f"line={line}"))
            continue
        source_id, kind, _, description = match.groups()
        ids.append(source_id)
        kinds.append(kind)
        if kind == "要確認" and description != "対応する主張を未確認。":
            errors.append(diagnostic("SOURCE_ENTRY_INVALID", f"S{source_id}_unverified_description"))
    duplicates = sorted({source_id for source_id in ids if ids.count(source_id) > 1}, key=int)
    for source_id in duplicates:
        errors.append(diagnostic("SOURCE_DUPLICATE_ID", f"S{source_id}"))
    if not ids:
        errors.append(diagnostic("SOURCE_MISSING", "no_valid_entries"))
    elif not any(kind in {"一次", "二次"} for kind in kinds):
        errors.append(diagnostic("SOURCE_UNVERIFIED", "no_primary_or_secondary"))
    known = set(ids)
    for source_id in sorted(set(re.findall(r"\[S([1-9][0-9]*)\]", before)), key=int):
        if source_id not in known:
            errors.append(diagnostic("SOURCE_ENTRY_INVALID", f"unknown_body_reference=S{source_id}"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    count = 0
    for path in args.paths:
        for item in validate(path):
            print(f"{item.code}  severity={item.severity}  category={item.category}  collection=insight  slug={path.stem}  reason={item.reason}")
            count += 1
    if count == 0:
        print("OK: insight外部ソース形式に問題なし")
    print(f"COUNT: {count}")
    return 1 if count else 0


if __name__ == "__main__":
    raise SystemExit(main())
