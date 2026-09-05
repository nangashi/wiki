#!/usr/bin/env python3
"""Maintain configured wiki indexes and report backlinks."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from config import Collection, ConfigError, load

SLUG = r"[a-z0-9][a-z0-9-]*"
ENTRY = re.compile(rf"^- \[\[({SLUG})\]\].*$", re.M)
LINK = re.compile(rf"\[\[(?:([a-z0-9][a-z0-9-]*):)?({SLUG})\]\]")


def fail(message: str) -> None:
    raise ValueError(message)


def page_path(collection: Collection, slug: str) -> Path:
    return collection.pages / f"{slug}.md"


def without_frontmatter_and_fences(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    start = 0
    if lines and lines[0] == "---":
        try:
            start = lines.index("---", 1) + 1
        except ValueError:
            pass
    result: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None
    for number, line in enumerate(lines[start:], start + 1):
        marker = re.match(r"^\s*([`~]{3,})", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            continue
        if fence is not None:
            if re.match(rf"^\s*{re.escape(fence[0])}{{{fence[1]},}}\s*$", line):
                fence = None
            continue
        result.append((number, line))
    return result


def overview_summary(path: Path) -> str:
    lines = without_frontmatter_and_fences(path.read_text(encoding="utf-8"))
    overview = next((i for i, (_, line) in enumerate(lines) if line.strip() == "## 概要"), None)
    if overview is None:
        fail(f"概要がありません: {path}")
    paragraph: list[str] = []
    for _, line in lines[overview + 1:]:
        if re.match(r"^#{1,6}\s", line) or (paragraph and not line.strip()):
            break
        if line.strip():
            paragraph.append(line.strip())
    if not paragraph:
        fail(f"概要が空です: {path}")
    return " ".join(paragraph)


def parse_spec(spec: str, collections: dict[str, Collection]) -> tuple[str, str]:
    collection, separator, slug = spec.partition(":")
    if separator != ":" or collection not in collections or not re.fullmatch(SLUG, slug):
        fail(f"collection:slug形式で登録済みcollectionを指定してください: {spec}")
    return collection, slug


def publication_allowed(root: Path, collection: Collection, slug: str) -> None:
    publication = collection.publication
    if publication.mode != "checked":
        return
    assert publication.command is not None
    result = subprocess.run([*publication.command, "--root", str(root), "--slug", slug], cwd=root)
    if result.returncode == 0:
        return
    if result.returncode == 1:
        fail(f"公開条件を満たさない記事は追加できません: {collection.id}:{slug}")
    fail(f"公開確認hookが失敗しました ({result.returncode}): {collection.id}:{slug}")


def render_index(root: Path, collection: Collection, additions: set[str], collections: dict[str, Collection]) -> str:
    if not collection.index.is_file():
        fail(f"indexがありません: {collection.index}")
    original = collection.index.read_text(encoding="utf-8")
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        slug = match.group(1)
        path = page_path(collection, slug)
        if not path.is_file():
            return ""
        seen.add(slug)
        return f"- [[{slug}]] — {overview_summary(path)}"

    rendered = ENTRY.sub(replace, original)
    missing = sorted(additions - seen)
    for slug in missing:
        path = page_path(collection, slug)
        if not path.is_file():
            fail(f"追加対象の記事がありません: {collection.id}:{slug}")
        duplicates = [other.id for other in collections.values()
                      if other.id != collection.id and page_path(other, slug).is_file()]
        if duplicates:
            fail(f"他collectionとslugが重複する記事は追加できません: {collection.id}:{slug} ({', '.join(duplicates)})")
        publication_allowed(root, collection, slug)
    if not missing:
        return rendered
    block = "\n".join(f"- [[{slug}]] — {overview_summary(page_path(collection, slug))}" for slug in missing)
    uncategorized = re.search(r"(?m)^## 未分類\s*$", rendered)
    if uncategorized:
        next_heading = re.search(r"(?m)^## ", rendered[uncategorized.end():])
        end = uncategorized.end() + (next_heading.start() if next_heading else len(rendered) - uncategorized.end())
        return rendered[:end].rstrip() + "\n\n" + block + "\n" + rendered[end:]
    return rendered.rstrip() + "\n\n## 未分類\n\n" + block + "\n"


def cmd_index(args: argparse.Namespace) -> int:
    root = args.root.resolve(); collections = load(root)
    additions = {name: set() for name in collections}
    for value in args.add:
        collection, slug = parse_spec(value, collections); additions[collection].add(slug)
    if args.collection and args.collection not in collections:
        fail(f"未登録collectionです: {args.collection}")
    if args.collection and any(name != args.collection and values for name, values in additions.items()):
        fail(f"--collection {args.collection} と--addのcollectionが一致しません")
    selected = [args.collection] if args.collection else list(collections)
    targets = {name: render_index(root, collections[name], additions[name], collections) for name in selected}
    changed = [name for name in selected if targets[name] != collections[name].index.read_text(encoding="utf-8")]
    if args.check:
        for name in changed: print(f"INDEX_OUTDATED {name}")
        return 1 if changed else 0
    for name in changed:
        collections[name].index.write_text(targets[name], encoding="utf-8")
        print(f"INDEX_UPDATED {name}")
    return 0


def cmd_backlinks(args: argparse.Namespace) -> int:
    root = args.root.resolve(); collections = load(root)
    target_collection, target_slug = parse_spec(args.target, collections)
    if not page_path(collections[target_collection], target_slug).is_file():
        fail(f"対象の記事がありません: {args.target}")
    matches: set[tuple[str, str, int]] = set()
    for source_collection, config in collections.items():
        if not config.pages.is_dir(): continue
        for source in sorted(config.pages.glob("*.md"), key=lambda path: path.stem):
            for number, line in without_frontmatter_and_fences(source.read_text(encoding="utf-8")):
                for prefix, slug in LINK.findall(line):
                    resolved = prefix or source_collection
                    if (resolved, slug) == (target_collection, target_slug):
                        matches.add((source_collection, source.stem, number))
    for collection, slug, number in sorted(matches): print(f"{collection}:{slug}:{number}")
    return 0


def cmd_collections(args: argparse.Namespace) -> int:
    for collection in load(args.root.resolve()).values():
        print(f"{collection.id}\t{collection.purpose}\t{collection.directory.relative_to(args.root.resolve())}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    index = sub.add_parser("index"); index.add_argument("--collection"); index.add_argument("--add", action="append", default=[]); index.add_argument("--check", action="store_true"); index.add_argument("--root", type=Path, default=Path.cwd()); index.set_defaults(func=cmd_index)
    backlinks = sub.add_parser("backlinks"); backlinks.add_argument("target"); backlinks.add_argument("--root", type=Path, default=Path.cwd()); backlinks.set_defaults(func=cmd_backlinks)
    listed = sub.add_parser("collections"); listed.add_argument("--root", type=Path, default=Path.cwd()); listed.set_defaults(func=cmd_collections)
    args = parser.parse_args()
    try: return args.func(args)
    except (OSError, ValueError, RuntimeError, ConfigError) as error:
        print(f"ERROR: {error}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
