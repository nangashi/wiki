#!/usr/bin/env python3
"""Collection-independent structural checks for registered wiki pages."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from config import ConfigError, load

LINK = re.compile(r"\[\[([^\]]+)\]\]")


def title(path: Path) -> str:
    match = re.search(r"(?m)^title:\s*[\"']?(.+?)[\"']?\s*$", path.read_text(encoding="utf-8"))
    return match.group(1) if match else path.stem


def content_lines(text: str) -> list[str]:
    """Return article lines outside a complete frontmatter block and fences."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0] == "---":
        try:
            start = lines.index("---", 1) + 1
        except ValueError:
            # Match wiki_structure: an unterminated opening marker is content.
            start = 0
    result: list[str] = []
    fence: tuple[str, int] | None = None
    for line in lines[start:]:
        marker = re.match(r"^\s*([`~]{3,})", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            continue
        if fence is not None:
            if re.match(rf"^\s*{re.escape(fence[0])}{{{fence[1]},}}\s*$", line):
                fence = None
            continue
        result.append(line)
    return result


def body(text: str) -> str:
    return "\n".join(content_lines(text))


def links(text: str) -> list[str]:
    return LINK.findall(body(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--collection", action="append", default=[])
    parser.add_argument("--checks", action="store_true", help="Run collection-configured check commands after common checks.")
    args = parser.parse_args()
    try:
        root = args.root.resolve(); configs = load(root)
        selected = args.collection or list(configs)
        unknown = [name for name in selected if name not in configs]
        if unknown: raise ConfigError(f"未登録collectionです: {unknown[0]}")
        # Preserve first occurrence when callers repeat --collection.
        selected = list(dict.fromkeys(selected))
        pages: dict[tuple[str, str], Path] = {}
        titles: dict[tuple[str, str], str] = {}
        for collection, config in configs.items():
            directory = config.pages
            for path in sorted(directory.glob("*.md")):
                if path.name == ".gitkeep": continue
                key = (collection, path.stem); pages[key] = path; titles[key] = title(path)
        selected_pages = {key: path for key, path in pages.items() if key[0] in selected}
        print(f"PAGES_TOTAL: {len(selected_pages)}")
        print(f"COLLECTIONS: {' '.join(selected)}\n")
        referred: set[tuple[str, str]] = set()
        parsed = {key: links(path.read_text(encoding="utf-8")) for key, path in pages.items()}
        if not selected_pages:
            print("INFO: ページが存在しません。共通チェックをスキップします。\n")
        print("=== CHECK-0: slug重複 ===")
        duplicate_count = 0
        by_slug: dict[str, list[str]] = {}
        for collection, slug in pages:
            by_slug.setdefault(slug, []).append(collection)
        for slug, collections in sorted(by_slug.items()):
            if len(collections) < 2:
                continue
            for collection in collections:
                if collection in selected:
                    print(f"DUPLICATE_SLUG  collection={collection}  slug={slug}  collections={','.join(collections)}")
                    duplicate_count += 1
        if not duplicate_count: print("OK: slug重複なし")
        print(f"COUNT: {duplicate_count}\n")
        print("=== CHECK-1: リンク切れ ===")
        count = 0
        for (collection, slug), refs in parsed.items():
            for ref in refs:
                if "|" in ref: continue
                target_collection, sep, target_slug = ref.partition(":")
                if not sep: target_collection, target_slug = collection, ref
                if (target_collection, target_slug) not in pages and collection in selected:
                    kind = "cross" if sep else "local"
                    print(f"BROKEN  collection={collection}  src={slug}  ref={ref}  type={kind}"); count += 1
                elif (target_collection, target_slug) in pages: referred.add((target_collection, target_slug))
        if not count: print("OK: リンク切れなし")
        print(f"COUNT: {count}\n")
        print("=== CHECK-1b: エイリアス記法 ===")
        aliases = 0
        for (collection, slug), refs in parsed.items():
            if collection not in selected: continue
            for ref in refs:
                if "|" in ref:
                    print(f"ALIAS  collection={collection}  src={slug}  link=[[{ref}]]"); aliases += 1
        if not aliases: print("OK: エイリアス記法なし")
        print(f"COUNT: {aliases}\n")
        print("=== CHECK-2: 孤立ページ ===")
        count = 0
        for key, path in selected_pages.items():
            if not parsed[key] and key not in referred:
                print(f"ORPHAN  collection={key[0]}  slug={key[1]}  title={titles[key]}"); count += 1
        if not count: print("OK: 孤立ページなし")
        print(f"COUNT: {count}\n")
        print("=== CHECK-3: リンク漏れ候補 (誤検知の可能性あり - LLMで最終確認) ===")
        count = 0
        for source, path in selected_pages.items():
            text = body(path.read_text(encoding="utf-8")); existing = set(parsed[source])
            for target, target_title in titles.items():
                if target[0] not in selected: continue
                if target == source or len(target_title) < 4 or target_title not in text: continue
                suggested = target[1] if target[0] == source[0] else f"{target[0]}:{target[1]}"
                if suggested not in existing:
                    print(f"MISSING_LINK  collection={source[0]}  src={source[1]}  mentions='{target_title}'  suggest=[[{suggested}]]"); count += 1
        if not count: print("OK: リンク漏れ候補なし")
        print(f"COUNT: {count}\n")
        print("=== CHECK-5: 粒度メトリクス (最終判断はLLMが行う) ===")
        count = 0
        for key, path in selected_pages.items():
            text = path.read_text(encoding="utf-8"); content = body(text); link_count = len(parsed[key]); sections = len(re.findall(r"(?m)^## ", text)); flags = []
            if len(content) > 2500: flags.append(f"LARGE({len(content)}chars)")
            if len(text) < 150: flags.append(f"TINY({len(text)}chars)")
            if link_count > 10: flags.append(f"MANY_LINKS({link_count})")
            if flags:
                print(f"METRICS  collection={key[0]}  slug={key[1]}  chars={len(text)}  body_chars={len(content)}  links={link_count}  sections={sections}  flags= {' '.join(flags)}"); count += 1
        if not count: print("OK: メトリクス異常なし")
        print(f"COUNT: {count}\n")
        print("=== CHECK-8: 低価値ページ候補 (最終判断はLLMが行う) ===")
        count = 0
        for key, path in selected_pages.items():
            text = path.read_text(encoding="utf-8"); content = body(text)
            if len(text) < 150 and not parsed[key] and key not in referred:
                print(f"LOW_VALUE  collection={key[0]}  slug={key[1]}  reason=TINY_ORPHAN  chars={len(text)}"); count += 1
            elif len(content) < 100 and re.search(r"→.*\[\[", content):
                print(f"LOW_VALUE  collection={key[0]}  slug={key[1]}  reason=REDIRECT  body_chars={len(content)}"); count += 1
        if not count: print("OK: 低価値ページ候補なし")
        print(f"COUNT: {count}\n")
        check_status = 0
        if args.checks:
            for collection in selected:
                for command in configs[collection].checks:
                    result = subprocess.run([*command, "--root", str(root)], cwd=root)
                    if result.returncode and not check_status:
                        check_status = result.returncode
        print("=== DONE ===")
        print("NOTE: CHECK-4(重複概念)・CHECK-6(矛盾) はLLM分析が必要")
        print("NOTE: CHECK-8 の候補はLLMが内容を確認し、削除前にユーザー確認を取ること")
        return check_status
    except (OSError, ValueError, ConfigError) as error:
        print(f"ERROR: {error}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
