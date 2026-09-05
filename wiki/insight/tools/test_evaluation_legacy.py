#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evaluation_state import queue_rank  # noqa: E402
from evaluation_validator_legacy import validate_text  # noqa: E402
from insight_source_validator import validate as validate_sources  # noqa: E402


def evaluation(slug: str = "sample", raw: str = "100", cap: str = "なし", final: str = "100",
               verdict: str = "公開品質", passed: str = "はい", blocking: str = "なし",
               major: str = "なし") -> str:
    rows = "\n".join([
        "| 核心と推論力 | 5 | 25 | 25 | 核心が明確。 |",
        "| 論理と構造 | 5 | 20 | 20 | 論理が接続する。 |",
        "| 有用性と適用境界 | 5 | 15 | 15 | 境界が明確。 |",
        "| 事実基盤 | 5 | 15 | 15 | 根拠を追跡できる。 |",
        "| 情報設計 | 5 | 10 | 10 | 自立して読める。 |",
        "| 日本語の自然さ | 5 | 15 | 15 | 自然に読める。 |",
    ])
    improvement = "- なし" if passed == "はい" else """### P1: 修正
- 対象箇所: 「対象」
- 問題: 問題がある。
- 改善後に満たす条件: 問題がなくなる。
- 改善方法: 修正する。
- 要外部調査: いいえ"""
    return f"""# Insight記事評価: {slug}

- reusability_gate: 合格
- raw_score: {raw}
- score_cap: {cap}
- final_score: {final}
- verdict: {verdict}
- pass: {passed}

## 再利用性ゲート
- R1: 推論できる。
- R2: 構造を再利用できる。
- R3: 該当なし。
- R4: 境界がある。

## 点数内訳
| 観点 | 0〜5 | 点数 | 配点 | 根拠 |
|---|---:|---:|---:|---|
{rows}

## Blocking
- {blocking}

## Major
- {major}

## Minor
- なし

## 改善項目
{improvement}

## 良い点
- 核心を保持する。
"""


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


class ValidatorTest(unittest.TestCase):
    def test_normal(self):
        self.assertTrue(validate_text(evaluation(), "sample")["valid"])

    def test_99_is_invalid(self):
        result = validate_text(evaluation(raw="99", final="99"), "sample")
        self.assertFalse(result["valid"])
        self.assertTrue(any("raw_score不一致" in value for value in result["errors"]))

    def test_sum_mismatch(self):
        broken = evaluation().replace("| 情報設計 | 5 | 10 |", "| 情報設計 | 5 | 8 |")
        self.assertFalse(validate_text(broken, "sample")["valid"])

    def test_cap_final_mismatch(self):
        result = validate_text(evaluation(cap="59", final="60", verdict="主要な修正が必要", passed="いいえ", blocking="重大な誤り。"), "sample")
        self.assertFalse(result["valid"])
        self.assertTrue(any("final_score" in value for value in result["errors"]))

    def test_blocking_pass_contradiction(self):
        result = validate_text(evaluation(cap="59", final="59", verdict="構造的な書き直しが必要", blocking="重大な誤り。"), "sample")
        self.assertFalse(result["valid"])
        self.assertTrue(any("pass" in value for value in result["errors"]))

    def test_missing_body_section(self):
        broken = evaluation().replace("## 良い点\n- 核心を保持する。\n", "")
        self.assertFalse(validate_text(broken, "sample")["valid"])


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
            rubric.write_text("**rubric_version: 1**\n", encoding="utf-8")
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
