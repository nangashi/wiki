#!/usr/bin/env python3
"""Run the insight-only source and evaluation-state checks.

This is intentionally separate from the collection-wide structural checker.
It uses the evaluation persistence helper as the single implementation of
metadata, output, and currency decisions.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from evaluation_state import current_rubric_version, git_blob, latest_evaluations, parse_metadata
from insight_source_validator import validate


def display_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def check_sources(pages: Path) -> None:
    print("=== CHECK-8b: insight外部ソース構造 ===")
    files = sorted(pages.glob("*.md"), key=lambda path: path.name) if pages.is_dir() else []
    if not files:
        print("INFO: insightページなし")
        print("COUNT: 0")
        print()
        return
    count = 0
    for path in files:
        for item in validate(path):
            print(f"{item.code}  severity={item.severity}  category={item.category}  collection=insight  slug={path.stem}  reason={item.reason}")
            count += 1
    if not count:
        print("OK: insight外部ソース形式に問題なし")
    else:
        print("INFO: insight外部ソース診断あり。lint全体は継続します")
    print(f"COUNT: {count}")
    print()


def check_evaluations(root: Path, pages: Path, evaluations: Path) -> None:
    print("=== CHECK-9: 記事品質評価状態 (insightコレクションのみ) ===")
    try:
        version = current_rubric_version(pages)
    except ValueError as error:
        print(f"WARN: {error}。CHECK-9 をスキップします")
        print()
        return

    records, invalid = latest_evaluations(pages, evaluations, version)
    by_slug = {record["slug"]: record for record in records}
    invalid_by_slug: dict[str, set[str]] = {}
    for item in invalid:
        invalid_by_slug.setdefault(item["slug"], set()).add(item["reason"])
        print(f"EVALUATION_HISTORY_WARNING  collection=insight  slug={item['slug']}  reason={item['reason']}  file={display_path(root, Path(item['file']))}")

    current = missing = old_rubric = changed = malformed = output = 0
    for page in sorted(pages.glob("*.md"), key=lambda path: path.stem):
        slug = page.stem
        record = by_slug[slug]
        invalid_reasons = invalid_by_slug.get(slug, set())
        if record["status"] == "current":
            metadata = parse_metadata(Path(record["file"]), slug)
            if metadata is None:
                raise RuntimeError(f"current evaluation metadata could not be read: {record['file']}")
            print("EVALUATION_CURRENT  collection=insight  slug={slug}  rubric={rubric}  blob={blob}  "
                  "evaluated_at={evaluated_at}  run_id={run_id}  latest={latest}".format(
                      slug=slug, rubric=record["rubric_version"], blob=metadata["target_blob"],
                      evaluated_at=metadata["evaluated_at"], run_id=metadata["run_id"],
                      latest=display_path(root, Path(record["file"]))))
            current += 1
        elif record["status"] == "legacy":
            print(f"EVALUATION_REQUIRED  collection=insight  slug={slug}  reason=rubric  evaluated_rubric={record['rubric_version']}  current_rubric={version}  latest={display_path(root, Path(record['file']))}")
            old_rubric += 1
        elif record["status"] == "changed":
            metadata = parse_metadata(Path(record["file"]), slug)
            if metadata is None:
                raise RuntimeError(f"changed evaluation metadata could not be read: {record['file']}")
            print(f"EVALUATION_REQUIRED  collection=insight  slug={slug}  reason=content  evaluated_blob={metadata['target_blob']}  current_blob={git_blob(page)}  latest={display_path(root, Path(record['file']))}")
            changed += 1
        elif "output" in invalid_reasons:
            print(f"EVALUATION_REQUIRED  collection=insight  slug={slug}  reason=output  current_rubric={version}")
            output += 1
        elif "metadata" in invalid_reasons:
            print(f"EVALUATION_REQUIRED  collection=insight  slug={slug}  reason=metadata  current_rubric={version}")
            malformed += 1
        else:
            print(f"EVALUATION_REQUIRED  collection=insight  slug={slug}  reason=missing  current_rubric={version}")
            missing += 1
    required = missing + old_rubric + changed + malformed + output
    invalid_metadata = sum(item["reason"] == "metadata" for item in invalid)
    invalid_output = sum(item["reason"] == "output" for item in invalid)
    print(f"EVALUATION_STATUS  rubric_version={version}  total={len(records)}  current={current}  missing={missing}  old_rubric={old_rubric}  content_changed={changed}  metadata_required={malformed}  output_required={output}  invalid_metadata_history={invalid_metadata}  invalid_output_history={invalid_output}  required={required}")
    if old_rubric:
        print(f"REEVALUATE_SCOPE  scope=all  reason=rubric_changed  count={len(records)}")
    elif required:
        print(f"REEVALUATE_SCOPE  scope=required  reason=missing_or_content_changed  count={required}")
    else:
        print("REEVALUATE_SCOPE  scope=none  reason=all_current  count=0")
        print("OK: 全insight記事の評価が現行rubric・現行内容と一致")
    print(f"COUNT: {required}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root directory does not exist: {root}", file=sys.stderr)
        return 2
    pages = root / "wiki" / "insight" / "pages"
    if not pages.is_dir():
        print(f"ERROR: insight pages directory does not exist: {pages}", file=sys.stderr)
        return 2
    try:
        # Resolve the required rubric before printing report-only findings.
        current_rubric_version(pages)
        check_sources(pages)
        check_evaluations(root, pages, root / "evaluations" / "insight")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print("=== DONE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
