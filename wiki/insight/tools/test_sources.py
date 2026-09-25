#!/usr/bin/env python3
"""External source validator tests (structure of the ## 外部ソース section)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evaluation_validator import CURRENT_RUBRIC_VERSION  # noqa: E402
from insight_source_validator import validate as validate_sources  # noqa: E402


def article(source_section: str) -> str:
    return f'''---
title: "テスト"
created: "2026-08-29"
updated: "2026-08-29"
---

# テスト

## 概要

テスト本文。

## 外部ソース

{source_section}
'''


class SourceValidatorTest(unittest.TestCase):
    def write(self, root: Path, name: str, source_section: str, frontmatter_extra: str = "") -> Path:
        path = root / name
        text = article(source_section)
        if frontmatter_extra:
            text = text.replace('title: "テスト"\n', f'title: "テスト"\n{frontmatter_extra}')
        path.write_text(text, encoding="utf-8")
        return path

    def cli(self, path: Path) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(HERE / "insight_source_validator.py"), str(path)],
                              text=True, capture_output=True)

    def test_exit_codes_for_diagnostics_and_normal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = {
                "missing.md": "外部ソース未確認。",
                "unverified.md": "- S1（要確認）: https://example.com — 対応する主張を未確認。",
                "invalid.md": "- S1（一次） https://example.com — 核心を支える。",
                "duplicate.md": "- S1（一次）: https://example.com/a — 核心を支える。\n- S1（二次）: https://example.com/b — 補足を支える。",
            }
            for name, section in fixtures.items():
                with self.subTest(name=name):
                    result = self.cli(self.write(root, name, section))
                    self.assertNotEqual(result.returncode, 0)
                    if name in {"missing.md", "unverified.md"}:
                        self.assertIn("severity=REQUIRED", result.stdout)
                        self.assertIn("category=quality", result.stdout)
                    else:
                        self.assertIn("severity=ERROR", result.stdout)
                        self.assertIn("category=structure", result.stdout)
            normal = self.cli(self.write(root, "normal.md", "- S1（一次）: https://example.com — 核心を支える。"))
            self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)

    def test_legacy_source_keys_all_forms(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, extra in enumerate((
                'source: "https://example.com"\n',
                'source:\n  - "https://example.com"\n',
                'sources: ["https://example.com"]\n',
                'sources:\n  - "https://example.com"\n',
            )):
                with self.subTest(extra=extra):
                    path = self.write(root, f"legacy-{index}.md", "- S1（一次）: https://example.com — 核心を支える。", extra)
                    errors = validate_sources(path)
                    self.assertTrue(any(item.code == "SOURCE_ENTRY_INVALID" and item.reason == "frontmatter_source_key_forbidden" for item in errors))
                    self.assertNotEqual(self.cli(path).returncode, 0)

    def test_nonsequential_ids_and_short_descriptions_are_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, section in (
                ("gapped", "- S2（一次）: https://example.com/a — 短い説明"),
                ("reordered", "- S9（一次）: https://example.com/a — a\n- S3（二次）: https://example.com/b — b"),
            ):
                with self.subTest(name=name):
                    path = self.write(root, f"{name}.md", section)
                    self.assertFalse(validate_sources(path))

    def test_empty_description_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(Path(directory), "empty.md", "- S1（一次）: https://example.com/a — ")
            errors = validate_sources(path)
            self.assertTrue(any(item.code == "SOURCE_ENTRY_INVALID" for item in errors))

    def test_undefined_body_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write(root, "undefined.md", "- S2（一次）: https://example.com/a — 根拠")
            path.write_text(path.read_text(encoding="utf-8").replace("テスト本文。", "テスト本文。[S1]"), encoding="utf-8")
            errors = validate_sources(path)
            self.assertTrue(any(item.reason == "unknown_body_reference=S1" for item in errors))

    def test_lint_continues_after_source_issue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "wiki/insight/pages"
            pages.mkdir(parents=True)
            self.write(pages, "bad.md", "外部ソース未確認。")
            rubric = root / "wiki/insight/references/article-quality-rubric.md"
            rubric.parent.mkdir()
            rubric.write_text(f"**rubric_version: {CURRENT_RUBRIC_VERSION}**\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            result = subprocess.run(
                [sys.executable, str(HERE / "check.py"), "--root", str(root)],
                cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SOURCE_MISSING", result.stdout)
            self.assertIn("insight外部ソース診断あり。lint全体は継続します", result.stdout)
            self.assertIn("=== DONE ===", result.stdout)



if __name__ == "__main__":
    unittest.main()
