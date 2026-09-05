#!/usr/bin/env python3
"""Maintain generated index summaries and report wiki backlinks.

The index is a view of already-public pages.  Adding a new insight page is the
only operation that consults evaluation history; an existing index entry keeps
its public status even when its evaluation later becomes stale.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


COLLECTIONS = ("insight", "it")
SLUG = r"[a-z0-9][a-z0-9-]*"
ENTRY = re.compile(rf"^- \[\[({SLUG})\]\].*$", re.M)
LINK = re.compile(rf"\[\[(?:(insight|it):)?({SLUG})\]\]")


def fail(message: str) -> None:
    raise ValueError(message)


def collection_paths(root: Path, collection: str) -> tuple[Path, Path]:
    return root / "wiki" / collection / "index.md", root / "wiki" / collection / "pages"


def page_path(root: Path, collection: str, slug: str) -> Path:
    return collection_paths(root, collection)[1] / f"{slug}.md"


def without_frontmatter_and_fences(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    start = 0
    if lines and lines[0] == "---":
        try:
            start = lines.index("---", 1) + 1
        except ValueError:
            start = 0
    result: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None
    for number, line in enumerate(lines[start:], start + 1):
        marker = re.match(r"^\s*([`~]{3,})", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            continue
        if fence is not None:
            close = re.match(rf"^\s*{re.escape(fence[0])}{{{fence[1]},}}\s*$", line)
            if close:
                fence = None
            continue
        if fence is None:
            result.append((number, line))
    return result


def overview_summary(path: Path) -> str:
    lines = without_frontmatter_and_fences(path.read_text(encoding="utf-8"))
    overview = next((i for i, (_number, line) in enumerate(lines) if line.strip() == "## 概要"), None)
    if overview is None:
        fail(f"概要がありません: {path}")
    paragraph: list[str] = []
    for _number, line in lines[overview + 1 :]:
        if re.match(r"^#{1,6}\s", line) or (paragraph and not line.strip()):
            break
        if line.strip():
            paragraph.append(line.strip())
    summary = " ".join(paragraph)
    if not summary:
        fail(f"概要が空です: {path}")
    return summary


def current_rubric_version(root: Path) -> int:
    rubric = root / "wiki" / "insight" / "references" / "article-quality-rubric.md"
    match = re.search(r"(?m)^\*\*rubric_version: ([0-9]+)\*\*\s*$", rubric.read_text(encoding="utf-8"))
    if not match:
        fail(f"rubric_versionが読めません: {rubric}")
    return int(match.group(1))


def evaluation_state_module() -> object:
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("wiki_structure_evaluation_state", here / "evaluation_state.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("evaluation_state.pyを読み込めません")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(here))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def approved_insight(root: Path, slug: str) -> bool:
    state = evaluation_state_module()
    pages = root / "wiki" / "insight" / "pages"
    records, _invalid = state.latest_evaluations(pages, root / "evaluations" / "insight")
    current = next((record for record in records if record["slug"] == slug), None)
    return bool(not state.validate_sources(page_path(root, "insight", slug)) and
                current and current.get("status") == "current" and
                current.get("rubric_version") == current_rubric_version(root) and
                current.get("pass") is True)


def parse_add(spec: str) -> tuple[str, str]:
    collection, separator, slug = spec.partition(":")
    if separator != ":" or collection not in COLLECTIONS or not re.fullmatch(SLUG, slug):
        fail(f"--addはcollection:slug形式です: {spec}")
    return collection, slug


def render_index(root: Path, collection: str, additions: set[str]) -> str:
    index, _pages = collection_paths(root, collection)
    if not index.is_file():
        fail(f"indexがありません: {index}")
    original = index.read_text(encoding="utf-8")
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        slug = match.group(1)
        path = page_path(root, collection, slug)
        if not path.is_file():
            return ""
        seen.add(slug)
        return f"- [[{slug}]] — {overview_summary(path)}"

    rendered = ENTRY.sub(replace, original)
    missing = sorted(additions - seen)
    if not missing:
        return rendered
    for slug in missing:
        path = page_path(root, collection, slug)
        if not path.is_file():
            fail(f"追加対象の記事がありません: {collection}:{slug}")
        if collection == "insight" and not approved_insight(root, slug):
            fail(f"未公開または不合格のinsight記事は追加できません: {slug}")
    block = "\n".join(f"- [[{slug}]] — {overview_summary(page_path(root, collection, slug))}" for slug in missing)
    uncategorized = re.search(r"(?m)^## 未分類\s*$", rendered)
    if uncategorized:
        next_heading = re.search(r"(?m)^## ", rendered[uncategorized.end():])
        end = uncategorized.end() + (next_heading.start() if next_heading else len(rendered) - uncategorized.end())
        return rendered[:end].rstrip() + "\n\n" + block + "\n" + rendered[end:]
    return rendered.rstrip() + "\n\n## 未分類\n\n" + block + "\n"


def cmd_index(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    additions: dict[str, set[str]] = {name: set() for name in COLLECTIONS}
    for value in args.add:
        collection, slug = parse_add(value)
        additions[collection].add(slug)
    selected = (args.collection,) if args.collection else COLLECTIONS
    if args.collection and any(collection != args.collection for collection in additions if additions[collection]):
        fail(f"--collection {args.collection} と--addのコレクションが一致しません")
    targets = {collection: render_index(root, collection, additions[collection]) for collection in selected}
    changed = [collection for collection in selected
               if targets[collection] != collection_paths(root, collection)[0].read_text(encoding="utf-8")]
    if args.check:
        for collection in changed:
            print(f"INDEX_OUTDATED {collection}")
        return 1 if changed else 0
    for collection in changed:
        collection_paths(root, collection)[0].write_text(targets[collection], encoding="utf-8")
        print(f"INDEX_UPDATED {collection}")
    return 0


def cmd_backlinks(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    target_collection, target_slug = parse_add(args.target)
    if not page_path(root, target_collection, target_slug).is_file():
        fail(f"対象の記事がありません: {args.target}")
    matches: set[tuple[str, str, int]] = set()
    for source_collection in COLLECTIONS:
        _index, pages = collection_paths(root, source_collection)
        for source in sorted(pages.glob("*.md"), key=lambda path: path.stem):
            for number, line in without_frontmatter_and_fences(source.read_text(encoding="utf-8")):
                for prefix, slug in LINK.findall(line):
                    resolved_collection = prefix or source_collection
                    if (resolved_collection, slug) == (target_collection, target_slug):
                        matches.add((source_collection, source.stem, number))
    for collection, slug, number in sorted(matches):
        print(f"{collection}:{slug}:{number}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    index = sub.add_parser("index")
    index.add_argument("--collection", choices=COLLECTIONS)
    index.add_argument("--add", action="append", default=[])
    index.add_argument("--check", action="store_true")
    index.add_argument("--root", type=Path, default=Path.cwd())
    index.set_defaults(func=cmd_index)
    backlinks = sub.add_parser("backlinks")
    backlinks.add_argument("target")
    backlinks.add_argument("--root", type=Path, default=Path.cwd())
    backlinks.set_defaults(func=cmd_backlinks)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
