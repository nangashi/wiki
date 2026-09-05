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
from evaluation_validator import validate_text  # noqa: E402
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


class StateTest(unittest.TestCase):
    def run_tool(self, cwd: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(HERE / "evaluation_state.py"), *args], cwd=cwd,
                              text=True, capture_output=True, check=True)

    def test_transitions_batch_limit_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "wiki/insight/pages"
            pages.mkdir(parents=True)
            for slug in ("delta", "alpha", "charlie", "bravo"):
                (pages / f"{slug}.md").write_text(
                    article("- S1（一次）: https://example.com/source — 核心を支える。"), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            manifest = root / "evaluations/insight/runs/run/manifest.json"
            self.run_tool(root, "init", "--manifest", str(manifest), "--rubric-version", "1", "--run-id", "abcdefgh", "--pages-dir", str(pages))
            first = self.run_tool(root, "next", "--manifest", str(manifest)).stdout
            self.assertEqual(first.count("EVALUATION_NEXT slug="), 3)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual([i["slug"] for i in data["items"]], ["alpha", "bravo", "charlie", "delta"])
            body = root / "alpha-evaluation.md"
            body.write_text(evaluation("alpha"), encoding="utf-8")
            self.run_tool(root, "save", "--manifest", str(manifest), "--slug", "alpha", "--body", str(body),
                          "--evaluations-root", str(root / "evaluations/insight"),
                          "--evaluated-at", "2026-08-29T00:00:00Z", "--evaluation-run-id", "ijklmnop")
            self.run_tool(root, "fail", "--manifest", str(manifest), "--slug", "bravo", "--error", "invalid")
            self.run_tool(root, "resume", "--manifest", str(manifest))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["items"][0]["status"], "success")
            self.assertEqual(data["items"][1]["status"], "retry")
            self.assertEqual(data["items"][2]["status"], "retry")
            second = self.run_tool(root, "next", "--manifest", str(manifest)).stdout
            self.assertEqual(second.count("EVALUATION_NEXT slug="), 3)
            self.run_tool(root, "fail", "--manifest", str(manifest), "--slug", "bravo", "--error", "invalid-again")
            self.run_tool(root, "resume", "--manifest", str(manifest))
            self.run_tool(root, "next", "--manifest", str(manifest))
            self.run_tool(root, "fail", "--manifest", str(manifest), "--slug", "bravo", "--error", "invalid-final")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["items"][1]["status"], "failed")
            self.assertEqual(data["items"][1]["attempts"], 3)
            self.assertTrue(manifest.with_suffix(".md").exists())

    def test_save_rejects_structural_source_issues(self):
        for name, section in (
            ("invalid", "- S1（一次） https://example.com — 核心を支える。"),
            ("duplicate", "- S1（一次）: https://example.com/a — 核心を支える。\n- S1（二次）: https://example.com/b — 補足を支える。"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                pages = root / "wiki/insight/pages"
                pages.mkdir(parents=True)
                (pages / f"{name}.md").write_text(article(section), encoding="utf-8")
                subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                manifest = root / "manifest.json"
                self.run_tool(root, "init", "--manifest", str(manifest), "--rubric-version", "1",
                              "--run-id", "abcdefgh", "--pages-dir", str(pages))
                self.run_tool(root, "next", "--manifest", str(manifest), "--limit", "1")
                body = root / "evaluation.md"
                body.write_text(evaluation(name), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(HERE / "evaluation_state.py"), "save", "--manifest", str(manifest),
                     "--slug", name, "--body", str(body), "--evaluations-root", str(root / "evaluations/insight")],
                    cwd=root, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("structurally invalid", result.stderr)
                self.assertFalse((root / f"evaluations/insight/{name}").exists())

    def test_missing_and_unverified_blocking_save_and_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "wiki/insight/pages"
            pages.mkdir(parents=True)
            (pages / "missing.md").write_text(article("外部ソース未確認。"), encoding="utf-8")
            (pages / "unverified.md").write_text(
                article("- S1（要確認）: https://example.com — 対応する主張を未確認。"), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            manifest = root / "manifest.json"
            evaluations_root = root / "evaluations/insight"
            self.run_tool(root, "init", "--manifest", str(manifest), "--rubric-version", "1",
                          "--run-id", "abcdefgh", "--pages-dir", str(pages))
            self.run_tool(root, "next", "--manifest", str(manifest), "--limit", "2")
            for index, slug in enumerate(("missing", "unverified")):
                body = root / f"{slug}-evaluation.md"
                source_code = "SOURCE_MISSING" if slug == "missing" else "SOURCE_UNVERIFIED"
                body.write_text(evaluation(slug, cap="49", final="49", verdict="構造的な書き直しが必要",
                                            passed="いいえ", blocking=f"{source_code}: 一次・二次ソースがない。"), encoding="utf-8")
                self.run_tool(root, "save", "--manifest", str(manifest), "--slug", slug, "--body", str(body),
                              "--evaluations-root", str(evaluations_root), "--evaluated-at", f"2026-08-29T00:00:0{index}Z",
                              "--evaluation-run-id", f"quality{index}a")
            normalized = root / "normalized.json"
            self.run_tool(root, "normalize", "--pages-dir", str(pages), "--evaluations-root", str(evaluations_root),
                          "--output", str(normalized))
            queue = json.loads(normalized.read_text(encoding="utf-8"))["improvement_queue"]
            self.assertEqual([item["slug"] for item in queue], ["missing", "unverified"])

    def test_missing_without_matching_blocking_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "wiki/insight/pages"
            pages.mkdir(parents=True)
            (pages / "missing.md").write_text(article("外部ソース未確認。"), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            manifest = root / "manifest.json"
            self.run_tool(root, "init", "--manifest", str(manifest), "--rubric-version", "1",
                          "--run-id", "abcdefgh", "--pages-dir", str(pages))
            self.run_tool(root, "next", "--manifest", str(manifest), "--limit", "1")
            body = root / "evaluation.md"
            body.write_text(evaluation("missing"), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(HERE / "evaluation_state.py"), "save", "--manifest", str(manifest),
                 "--slug", "missing", "--body", str(body), "--evaluations-root", str(root / "evaluations/insight")],
                cwd=root, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires a matching Blocking", result.stderr)
            self.assertFalse((root / "evaluations/insight/missing").exists())

    def test_stable_queue(self):
        records = [
            {"slug": "z", "final_score": 50, "blocking_count": 0, "major_count": 0},
            {"slug": "b", "final_score": 40, "blocking_count": 1, "major_count": 0},
            {"slug": "a", "final_score": 40, "blocking_count": 1, "major_count": 0},
            {"slug": "m", "final_score": 80, "blocking_count": 0, "major_count": 1},
        ]
        self.assertEqual([r["slug"] for r in sorted(records, key=queue_rank)], ["a", "b", "m", "z"])

    def test_lint_does_not_sample_when_all_evaluations_are_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "wiki/insight/pages"
            pages.mkdir(parents=True)
            (pages / "current.md").write_text(
                article("- S1（一次）: https://example.com/source — 根拠"), encoding="utf-8")
            rubric = root / "rubric.md"
            rubric.write_text("**rubric_version: 1**\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            manifest = root / "manifest.json"
            evaluations_root = root / "evaluations/insight"
            self.run_tool(root, "init", "--manifest", str(manifest), "--rubric-version", "1",
                          "--run-id", "abcdefgh", "--pages-dir", str(pages))
            self.run_tool(root, "next", "--manifest", str(manifest), "--limit", "1")
            body = root / "evaluation.md"
            body.write_text(evaluation("current"), encoding="utf-8")
            self.run_tool(root, "save", "--manifest", str(manifest), "--slug", "current", "--body", str(body),
                          "--evaluations-root", str(evaluations_root), "--evaluated-at", "2026-08-29T00:00:00Z",
                          "--evaluation-run-id", "ijklmnop")
            result = subprocess.run(
                ["bash", str(HERE / "lint-check.sh"), "--collection", f"insight:{pages}",
                 "--evaluations-root", str(evaluations_root), "--rubric-file", str(rubric)],
                cwd=root, text=True, capture_output=True, check=True)
            self.assertIn("REEVALUATE_SCOPE  scope=none  reason=all_current  count=0", result.stdout)
            self.assertNotIn("SAMPLE_EVALUATION", result.stdout)


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
                        self.assertIn("severity=BLOCKING", result.stdout)
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
            pages = root / "pages"
            pages.mkdir()
            self.write(pages, "bad.md", "外部ソース未確認。")
            rubric = root / "rubric.md"
            rubric.write_text("**rubric_version: 1**\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            result = subprocess.run(
                ["bash", str(HERE / "lint-check.sh"), "--collection", f"insight:{pages}",
                 "--evaluations-root", str(root / "evaluations"), "--rubric-file", str(rubric)],
                cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SOURCE_MISSING", result.stdout)
            self.assertIn("insight外部ソース診断あり。lint全体は継続します", result.stdout)
            self.assertIn("=== DONE ===", result.stdout)


class WorkflowContractTest(unittest.TestCase):
    def test_ingest_rejects_all_source_diagnostics_for_publication(self):
        skill = (HERE.parent / "ingest/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("categoryを問わず診断が1件でもあれば", skill)
        self.assertIn("`pages/`への正式配置・評価済み扱い・index追加へ進まない", skill)


if __name__ == "__main__":
    unittest.main()
