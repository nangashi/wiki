#!/usr/bin/env python3
"""Meaningful integration tests for wiki_structure.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "wiki_structure.py"


class WikiStructureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for collection in ("insight", "it"):
            (self.root / "wiki" / collection / "pages").mkdir(parents=True)
        (self.root / "wiki" / "insight" / "references").mkdir(parents=True)
        (self.root / "wiki" / "insight" / "references" / "article-quality-rubric.md").write_text(
            "# rubric\n\n**rubric_version: 2**\n", encoding="utf-8")
        self.write_index("insight", "# Index\n\n## A\n\n- [[kept]] — 古い要約\n- [[gone]] — 消える\n\n## B\n\n- [[draft]] — 既存公開\n")
        self.write_index("it", "# IT\n\n## Existing\n\n- [[target]] — 古い\n- [[fenced-overview]] — 古い\n")
        self.write_page("insight", "kept", "保持したい概要\n次の行も同じ段落。")
        self.write_page("insight", "draft", "既存掲載は評価不一致でも残る。")
        self.write_page("insight", "new-pass", "合格済みの新規記事。")
        self.write_page("insight", "new-fail", "不合格の新規記事。")
        self.write_page("insight", "new-draft", "評価のない草稿。")
        self.write_page("insight", "new-old-rubric", "古いrubricの評価。")
        self.write_page("insight", "new-stale", "古い本文の評価。")
        self.write_page("it", "target", "対象ページ。")
        (self.root / "wiki/it/pages/fenced-overview.md").write_text(
            "---\ntitle: x\n---\n\n# fenced\n\n````md\n## 概要\n\n偽の概要。\n```\n````\n\n## 概要\n\n実際の概要。\n\n## 詳細\n\ntext\n",
            encoding="utf-8")
        self.write_page("it", "source", "[[target]]\n[[insight:kept]]\n````md\n[[target]]\n```\n~~~\n[[target]]\n````\n[[target]] [[target]]\n")
        self.write_page("insight", "cross", "[[it:target]]\n[[kept]]\n")
        self.init_git()
        self.write_evaluation("new-pass", passed=True)
        self.write_evaluation("new-fail", passed=False)
        self.write_evaluation("new-old-rubric", passed=True, rubric_version=1)
        self.write_evaluation("new-stale", passed=True)
        stale = self.root / "wiki/insight/pages/new-stale.md"
        stale.write_text(stale.read_text(encoding="utf-8").replace("古い本文", "更新後の本文"), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_index(self, collection: str, text: str) -> None:
        (self.root / "wiki" / collection / "index.md").write_text(text, encoding="utf-8")

    def write_page(self, collection: str, slug: str, overview: str) -> None:
        sources = "\n## 外部ソース\n\n- S1（二次）: https://example.test/source — 概要の根拠。\n" if collection == "insight" else ""
        (self.root / "wiki" / collection / "pages" / f"{slug}.md").write_text(
            f"---\ntitle: x\n---\n\n# {slug}\n\n## 概要\n\n{overview}\n\n## 詳細\n\ntext\n{sources}", encoding="utf-8")

    def init_git(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "wiki"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qm", "init"], cwd=self.root, check=True)

    def write_evaluation(self, slug: str, passed: bool, rubric_version: int = 2) -> None:
        major = "- 評価上の主要な不足。" if not passed else "- なし"
        improvements = """### P1: 主要な不足を解消する

- 対象箇所: 本文
- 問題: 根拠が不足する
- 改善後に満たす条件: 根拠が示される
- 改善方法: 根拠を追加する
- 要外部調査: いいえ""" if not passed else "- なし"
        body = """# Insight記事評価: {slug}

- reusability_gate: 合格
- raw_score: 80
- score_cap: なし
- final_score: 80
- verdict: 良好。軽微な改善のみ
- pass: {passed}

## 再利用性ゲート

- R1: x
- R2: x
- R3: x
- R4: x

## 点数内訳

| 観点 | 0〜5 | 換算点 | 配点 | 根拠 |
|---|---:|---:|---:|---|
| 核心と推論力 | 4 | 20 | 25 | x |
| 論理と構造 | 4 | 16 | 20 | x |
| 有用性と適用境界 | 4 | 12 | 15 | x |
| 事実基盤 | 4 | 12 | 15 | x |
| 情報設計 | 4 | 8 | 10 | x |
| 日本語の自然さ | 4 | 12 | 15 | x |

## Blocking

- なし

## Major

{major}

## Minor

- なし

## 改善項目

{improvements}

## 良い点

- x
""".format(slug=slug, passed="はい" if passed else "いいえ", major=major, improvements=improvements)
        blob = subprocess.run(["git", "hash-object", f"wiki/insight/pages/{slug}.md"], cwd=self.root,
                              check=True, text=True, capture_output=True).stdout.strip()
        path = self.root / "evaluations" / "insight" / slug / f"20260101T000000Z-v{rubric_version}-abcdefgh.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\n" + f'target: "wiki/insight/pages/{slug}.md"\n' +
                        f'target_blob: "{blob}"\n' + f'rubric_version: {rubric_version}\n' +
                        'evaluator: "codex"\nevaluator_model: "gpt-5.6-sol"\n' +
                        'evaluated_at: "2026-01-01T00:00:00Z"\nrun_id: "abcdefgh"\n---\n' + body, encoding="utf-8")

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args, "--root", str(self.root)], cwd=self.root,
                              text=True, capture_output=True)

    def test_index_preserves_categories_is_idempotent_and_drops_missing(self) -> None:
        result = self.invoke("index", "--collection", "insight")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.root / "wiki/insight/index.md").read_text(encoding="utf-8")
        self.assertIn("## A", text); self.assertIn("## B", text)
        self.assertIn("- [[kept]] — 保持したい概要 次の行も同じ段落。", text)
        self.assertIn("- [[draft]] — 既存掲載は評価不一致でも残る。", text)
        self.assertNotIn("gone", text)
        self.assertEqual(self.invoke("index", "--collection", "insight").returncode, 0)
        self.assertEqual(self.invoke("index", "--collection", "insight", "--check").returncode, 0)
        before = (self.root / "wiki/it/index.md").read_text(encoding="utf-8")
        mismatch = self.invoke("index", "--collection", "it", "--add", "insight:new-pass")
        self.assertEqual(mismatch.returncode, 2)
        self.assertEqual((self.root / "wiki/it/index.md").read_text(encoding="utf-8"), before)

    def test_overview_ignores_fenced_headings_and_rejects_empty_section(self) -> None:
        indexed = self.invoke("index", "--collection", "it")
        self.assertEqual(indexed.returncode, 0, indexed.stderr)
        text = (self.root / "wiki/it/index.md").read_text(encoding="utf-8")
        self.assertIn("- [[fenced-overview]] — 実際の概要。", text)
        empty = self.root / "wiki/it/pages/empty-overview.md"
        empty.write_text("# empty\n\n## 概要\n\n### 補足\n\n本文。\n", encoding="utf-8")
        before = (self.root / "wiki/it/index.md").read_text(encoding="utf-8")
        rejected = self.invoke("index", "--collection", "it", "--add", "it:empty-overview")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual((self.root / "wiki/it/index.md").read_text(encoding="utf-8"), before)

    def test_new_insight_requires_current_passing_evaluation(self) -> None:
        before = (self.root / "wiki/insight/index.md").read_text(encoding="utf-8")
        failed = self.invoke("index", "--collection", "insight", "--add", "insight:new-fail")
        self.assertEqual(failed.returncode, 2)
        self.assertEqual((self.root / "wiki/insight/index.md").read_text(encoding="utf-8"), before)
        draft = self.invoke("index", "--collection", "insight", "--add", "insight:new-draft")
        self.assertEqual(draft.returncode, 2)
        self.assertEqual((self.root / "wiki/insight/index.md").read_text(encoding="utf-8"), before)
        for slug in ("new-old-rubric", "new-stale"):
            rejected = self.invoke("index", "--collection", "insight", "--add", f"insight:{slug}")
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual((self.root / "wiki/insight/index.md").read_text(encoding="utf-8"), before)
        passed = self.invoke("index", "--collection", "insight", "--add", "insight:new-pass", "--add", "insight:new-pass")
        self.assertEqual(passed.returncode, 0, passed.stderr)
        text = (self.root / "wiki/insight/index.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("[[new-pass]]"), 1)
        self.assertIn("## 未分類", text)

    def test_backlinks_resolve_direction_cross_links_and_do_not_change_articles(self) -> None:
        before = (self.root / "wiki/it/pages/source.md").read_text(encoding="utf-8")
        result = self.invoke("backlinks", "it:target")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["insight:cross:9", "it:source:9", "it:source:17"])
        self.assertEqual((self.root / "wiki/it/pages/source.md").read_text(encoding="utf-8"), before)
        self.assertEqual(self.invoke("backlinks", "insight:kept").stdout.splitlines(), ["insight:cross:10", "it:source:10"])


if __name__ == "__main__":
    unittest.main()
