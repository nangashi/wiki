#!/usr/bin/env python3
"""Publication admission tests recovered from the former index integration tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_evaluation_tools import EVALS, action, design_body, ev, write_design_pair, write_rubrics
from evaluation_validator import CURRENT_RUBRIC_VERSION as V
from design_evaluation_validator import CURRENT_RUBRIC_VERSION as DV

PUBLICATION = HERE / "publication.py"
CHECK = HERE / "check.py"


class PublicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pages = self.root / "wiki/insight/pages"
        self.pages.mkdir(parents=True)
        write_rubrics(self.root)
        self.write_page("current")
        self.write_page("changed")
        self.write_page("legacy")
        self.write_page("source-malformed", source="外部ソース未確認。")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.write_evaluation("current")
        self.write_evaluation("changed")
        self.write_evaluation("legacy", rubric_version=V - 1)
        changed = self.pages / "changed.md"
        changed.write_text(changed.read_text(encoding="utf-8") + "更新。\n", encoding="utf-8")
        self.write_evaluation("source-malformed")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_page(self, slug: str, source: str = "- S1（二次）: https://example.test/source — 概要の根拠。") -> None:
        (self.pages / f"{slug}.md").write_text(
            f"---\ntitle: x\n---\n\n# {slug}\n\n## 概要\n\n公開条件を検証する。\n\n## 外部ソース\n\n{source}\n",
            encoding="utf-8")

    def write_evaluation(self, slug: str, rubric_version: int = V) -> Path:
        """Write the page's design pair and an article evaluation that references it."""
        from evaluation_state import git_blob
        history = write_design_pair(self.root, slug)
        design = self.root / "wiki/insight/designs" / f"{slug}.md"
        destination = self.root / EVALS / slug / "article.md"
        destination.write_text(
            "---\n"
            f'target: "wiki/insight/pages/{slug}.md"\n'
            f'target_blob: "{git_blob(self.pages / f"{slug}.md")}"\n'
            f'design_target: "wiki/insight/designs/{slug}.md"\n'
            f'design_blob: "{git_blob(design)}"\n'
            f'design_evaluation_blob: "{git_blob(history)}"\n'
            f"rubric_version: {rubric_version}\n"
            'evaluator: "claude"\n'
            'evaluator_model: "opus"\n'
            'evaluated_at: "2026-01-01T00:00:00Z"\n'
            'run_id: "abcdefgh"\n'
            "round: 1\n"
            "---\n" + ev().replace("# Insight記事評価: sample", f"# Insight記事評価: {slug}"), encoding="utf-8")
        return destination

    def pair(self, slug="current"):
        design = self.root / "wiki/insight/designs" / f"{slug}.md"
        return design, self.root / EVALS / slug / "design.md", self.root / EVALS / slug / "article.md"

    def invoke(self, slug: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(PUBLICATION), "--root", str(self.root), "--slug", slug], text=True, capture_output=True)

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CHECK), "--root", str(self.root)], text=True, capture_output=True)

    def test_current_pair_allows_and_design_change_invalidates(self):
        design, _, _ = self.pair()
        self.assertEqual(self.invoke("current").returncode, 0)
        design.write_text(design.read_text() + "新しい条件。\n")
        self.assertEqual(self.invoke("current").returncode, 1)
        from evaluation_state import latest_evaluations
        records, _ = latest_evaluations(self.pages, self.root / EVALS)
        current = next(r for r in records if r["slug"] == "current")
        self.assertNotEqual(current["design_state"], "complete")
        self.assertNotEqual(current["status"], "current")

    def test_failed_alignment_cannot_publish(self):
        _, _, article_eval = self.pair()
        article_eval.write_text(article_eval.read_text().replace("design_alignment: 合格", "design_alignment: 不合格")
                                .replace("## 対応項目\n- なし", "## 対応項目\n" + action(d="情報設計"))
                                .replace("| 情報設計 | 十分 |", "| 情報設計 | 要対応 |"))
        self.assertEqual(self.invoke("current").returncode, 1)

    def test_replaced_design_evaluation_invalidates_old_pair(self):
        _, history, _ = self.pair()
        text = history.read_text().replace("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z").replace('run_id: "design01"', 'run_id: "design02"')
        history.write_text(text.split("---\n", 2)[0] + "---\n" + text.split("---\n", 2)[1] + "---\n" +
                           design_body("current", "要対応", action(d="読者・目的")))
        self.assertEqual(self.invoke("current").returncode, 1)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("slug=current reason=quality", result.stdout)

    def test_deleted_design_requires_design_again(self):
        design, _, _ = self.pair()
        design.unlink()
        self.assertEqual(self.invoke("current").returncode, 1)
        self.assertIn("ARTICLE_DESIGN_STATE collection=insight slug=current state=required", self.check().stdout)

    def test_design_rubric_mismatch_is_error(self):
        (self.root / "wiki/insight/references/design-quality-rubric.md").write_text(f"**design_rubric_version: {DV + 1}**\n")
        self.assertEqual(self.invoke("current").returncode, 2)

    def test_legacy_design_evaluation_is_not_current(self):
        from evaluation_state import latest_design_evaluations
        _, history, _ = self.pair()
        history.write_text(history.read_text().replace(f"rubric_version: {DV}", f"rubric_version: {DV - 1}"))
        records, invalid = latest_design_evaluations(self.root / "wiki/insight/designs", self.root / EVALS)
        self.assertFalse(invalid)
        self.assertEqual(next(r for r in records if r["slug"] == "current")["status"], "legacy")
        self.assertEqual(self.invoke("current").returncode, 1)
        rejected = self.state_tool("init", "--rubric-version", str(V), "--manifest", str(self.root / "legacy.json"),
                                   "--target", "current:wiki/insight/pages/current.md")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn(f"design rubric_version={DV}", rejected.stderr)

    def test_article_init_requires_design_application_test(self):
        design, _, _ = self.pair()
        design.write_text(design.read_text().replace("- 適用テスト: 新しい状況。→ 判断する。\n", ""))
        write_design_pair(self.root, "current")
        rejected = self.state_tool("init", "--rubric-version", str(V), "--manifest", str(self.root / "no-test.json"),
                                   "--target", "current:wiki/insight/pages/current.md")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("適用テスト", rejected.stderr)

    def state_tool(self, *args):
        if args and args[0] == "save":
            if "--stage1" not in args:
                body = Path(args[args.index("--body") + 1]).read_text(encoding="utf-8")
                section = body.split("## 記事単独読解", 1)[1].split("\n## ", 1)[0] if "## 記事単独読解" in body else ""
                stage1 = self.root / "stage1.md"
                stage1.write_text(section, encoding="utf-8")
                args = (*args, "--stage1", str(stage1))
            if "--round" not in args:
                args = (*args, "--round", "1")
        return subprocess.run([sys.executable, str(HERE / "evaluation_state.py"), *args],
                              cwd=self.root, text=True, capture_output=True)

    def claim_article(self):
        manifest = self.root / "manifest.json"
        init = self.state_tool("init", "--rubric-version", str(V), "--manifest", str(manifest),
                               "--target", "current:wiki/insight/pages/current.md")
        self.assertEqual(init.returncode, 0, init.stderr)
        result = self.state_tool("next", "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        return manifest

    def test_design_change_after_claim_rejects_article_save_and_resume_marks_it(self):
        import json
        design, _, article_eval = self.pair()
        manifest = self.claim_article()
        body = self.root / "body.md"
        body.write_text(article_eval.read_text().split("---\n", 2)[2])
        design.write_text(design.read_text() + "変更。\n")
        result = self.state_tool("save", "--manifest", str(manifest), "--slug", "current", "--body", str(body))
        self.assertNotEqual(result.returncode, 0)
        resumed = self.state_tool("resume", "--manifest", str(manifest))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(json.loads(manifest.read_text())["items"][0]["error"], "design changed")

    def test_article_init_rejects_missing_design_and_save_rejects_missing_outcome(self):
        _, history, article_eval = self.pair()
        body = self.root / "body.md"
        body.write_text(article_eval.read_text().split("---\n", 2)[2])
        manifest = self.claim_article()
        body.write_text(body.read_text().replace("- D1:", "- D2:"))
        result = self.state_tool("save", "--manifest", str(manifest), "--slug", "current", "--body", str(body))
        self.assertNotEqual(result.returncode, 0)
        history.unlink()
        fresh = self.root / "unclaimed.json"
        rejected = self.state_tool("init", "--rubric-version", str(V), "--manifest", str(fresh),
                                   "--target", "current:wiki/insight/pages/current.md")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(fresh.exists())

    def test_missing_design_without_evaluations_requires_design(self):
        import shutil
        (self.root / "wiki/insight/designs/current.md").unlink()
        shutil.rmtree(self.root / EVALS)
        manifest = self.root / "fresh.json"
        result = self.state_tool("init", "--rubric-version", str(V), "--manifest", str(manifest),
                                 "--target", "current:wiki/insight/pages/current.md")
        self.assertNotEqual(result.returncode, 0)
        result = self.check()
        self.assertIn("ARTICLE_DESIGN_STATE collection=insight slug=current state=required", result.stdout)
        self.assertIn("DESIGN_EVALUATION_REQUIRED collection=insight slug=current reason=missing", result.stdout)

    def test_design_init_and_next_do_not_write_wiki_json(self):
        manifest = self.root / ".cache/insight-runs/d/manifest.json"
        result = self.state_tool("init", "--kind", "design", "--rubric-version", str(DV), "--manifest", str(manifest),
                                 "--target", "current:wiki/insight/designs/current.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.state_tool("next", "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list((self.root / "wiki/insight").rglob("*.json")), [])

    def test_legacy_article_evaluation_cannot_be_newly_published(self) -> None:
        from evaluation_state import latest_evaluations
        records, invalid = latest_evaluations(self.pages, self.root / EVALS)
        legacy = next(record for record in records if record["slug"] == "legacy")
        self.assertEqual(legacy["status"], "legacy")
        self.assertEqual(legacy["rubric_version"], V - 1)
        self.assertFalse(invalid)
        result = self.invoke("legacy")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("INSIGHT_PUBLICATION DENY", result.stdout)

    def test_changed_and_malformed_sources_are_denied(self) -> None:
        for slug in ("changed", "source-malformed", "missing"):
            with self.subTest(slug=slug):
                result = self.invoke(slug)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("INSIGHT_PUBLICATION DENY", result.stdout)

    def test_missing_rubric_and_root_inputs_are_errors(self) -> None:
        rubric = self.root / "wiki/insight/references/article-quality-rubric.md"
        rubric.unlink()
        result = self.invoke("current")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR:", result.stderr)
        missing_root = self.root / "missing-root"
        check = subprocess.run([sys.executable, str(CHECK), "--root", str(missing_root)], text=True, capture_output=True)
        self.assertEqual(check.returncode, 2)
        self.assertIn("ERROR:", check.stderr)

        with tempfile.TemporaryDirectory() as empty:
            missing_pages = subprocess.run([sys.executable, str(CHECK), "--root", empty], text=True, capture_output=True)
        self.assertEqual(missing_pages.returncode, 2)
        self.assertIn("insight pages directory", missing_pages.stderr)

    def test_check_missing_rubric_is_error(self) -> None:
        (self.root / "wiki/insight/references/article-quality-rubric.md").unlink()
        result = self.check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR:", result.stderr)


if __name__ == "__main__":
    unittest.main()
