#!/usr/bin/env python3
"""Publication admission tests recovered from the former index integration tests."""

from __future__ import annotations

import subprocess
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_evaluation_tools import ev

PUBLICATION = HERE / "publication.py"
CHECK = HERE / "check.py"


class PublicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pages = self.root / "wiki/insight/pages"
        self.pages.mkdir(parents=True)
        references = self.root / "wiki/insight/references"
        references.mkdir()
        (references / "design-quality-rubric.md").write_text("**design_rubric_version: 1**\n", encoding="utf-8")
        (references / "article-quality-rubric.md").write_text("**rubric_version: 6**\n", encoding="utf-8")
        (self.root / "wiki/insight/design-migration.json").write_text(json.dumps({"schema_version": 1, "legacy_slugs": ["current", "changed", "legacy", "source-malformed"]}), encoding="utf-8")
        self.write_page("current")
        self.write_page("changed")
        self.write_page("legacy")
        self.write_page("source-malformed", source="外部ソース未確認。")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.write_evaluation("current")
        self.write_evaluation("changed")
        self.write_evaluation("legacy", rubric_version=3)
        changed = self.pages / "changed.md"
        changed.write_text(changed.read_text(encoding="utf-8") + "更新。\n", encoding="utf-8")
        self.write_evaluation("source-malformed")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_page(self, slug: str, source: str = "- S1（二次）: https://example.test/source — 概要の根拠。") -> None:
        (self.pages / f"{slug}.md").write_text(
            f"---\ntitle: x\n---\n\n# {slug}\n\n## 概要\n\n公開条件を検証する。\n\n## 外部ソース\n\n{source}\n",
            encoding="utf-8")

    def write_evaluation(self, slug: str, rubric_version: int = 6) -> None:
        page = self.pages / f"{slug}.md"
        blob = subprocess.run(["git", "hash-object", str(page)], check=True, text=True, capture_output=True).stdout.strip()
        destination = self.root / "evaluations/insight" / slug / f"20260101T000000Z-v{rubric_version}-abcdefgh.md"
        destination.parent.mkdir(parents=True)
        destination.write_text(
            "---\n"
            f'target: "wiki/insight/pages/{slug}.md"\n'
            f'target_blob: "{blob}"\n'
            f"rubric_version: {rubric_version}\n"
            'evaluator: "codex"\n'
            'evaluator_model: "gpt-5.6-sol"\n'
            'evaluated_at: "2026-01-01T00:00:00Z"\n'
            'run_id: "abcdefgh"\n'
            "---\n" + ev(version=rubric_version), encoding="utf-8")
        # The shared fixture is fixed to slug=sample; make the persisted evaluation valid for this page.
        destination.write_text(destination.read_text(encoding="utf-8").replace("# Insight記事評価: sample", f"# Insight記事評価: {slug}"), encoding="utf-8")

    def add_design_pair(self, slug="current"):
        from evaluation_state import git_blob
        from design_evaluation_validator import DIMENSIONS
        designs = self.root / "wiki/insight/designs"
        designs.mkdir(exist_ok=True)
        design = designs / f"{slug}.md"
        design.write_text("# Design\n" + "\n".join(
            f"## {name}\n" + ("- D1: 判断する。" if name == "読後の到達点" else "説明。")
            for name in DIMENSIONS) + "\n")
        history = self.root / "evaluations/insight" / slug / "design" / "20260101T000000Z-v1-design01.md"
        history.parent.mkdir(parents=True, exist_ok=True)
        metadata = (f'---\ntarget: "wiki/insight/designs/{slug}.md"\n'
                    f'target_blob: "{git_blob(design)}"\nrubric_version: 1\n'
                    'evaluator: "codex"\nevaluator_model: "gpt-5.6-sol"\n'
                    'evaluated_at: "2026-01-01T00:00:00Z"\nrun_id: "design01"\n---\n')
        body = (f"# Insight設計評価: {slug}\n- reusability_gate: 合格\n"
                "## 再利用性ゲート\n- R1: a\n- R2: b\n- R3: c\n- R4: d\n"
                "## 観点別評価\n| 観点 | 状態 | 根拠 |\n|---|---|---|\n" +
                "\n".join(f"| {name} | 十分 | 根拠。 |" for name in DIMENSIONS) +
                "\n## 対応項目\n- なし\n## 良い点\n- 明確。\n")
        history.write_text(metadata + body)
        article_eval = self.root / "evaluations/insight" / slug / "20260101T000000Z-v6-abcdefgh.md"
        text = article_eval.read_text().replace('rubric_version: 6\n',
            f'rubric_version: 6\ndesign_target: "wiki/insight/designs/{slug}.md"\n'
            f'design_blob: "{git_blob(design)}"\ndesign_evaluation: "{history}"\n')
        article_eval.write_text(text.replace("- design_alignment: 未導入", "- design_alignment: 合格\n- D1: 本文で判断できる。"))
        return design, history, article_eval

    def test_current_pair_allows_and_design_change_invalidates(self):
        design, history, article_eval = self.add_design_pair()
        self.assertEqual(self.invoke("current").returncode, 0)
        design.write_text(design.read_text() + "新しい条件。\n")
        self.assertEqual(self.invoke("current").returncode, 1)
        from evaluation_state import latest_evaluations
        records, _ = latest_evaluations(self.pages, self.root / "evaluations/insight")
        current = next(r for r in records if r["slug"] == "current")
        self.assertNotEqual(current["design_state"], "complete")
        self.assertNotEqual(current["status"], "current")

    def test_failed_alignment_cannot_publish(self):
        _, _, article_eval = self.add_design_pair()
        article_eval.write_text(article_eval.read_text().replace("design_alignment: 合格", "design_alignment: 不合格"))
        self.assertEqual(self.invoke("current").returncode, 1)

    def test_newer_failed_design_invalidates_old_pair(self):
        from test_evaluation_tools import action
        _, history, _ = self.add_design_pair()
        failed = history.with_name("20260102T000000Z-v1-design02.md")
        text = history.read_text().replace("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z").replace('run_id: "design01"', 'run_id: "design02"')
        text = text.replace("| 読者・目的 | 十分 |", "| 読者・目的 | 要対応 |")
        failed.write_text(text.replace("## 対応項目\n- なし", "## 対応項目\n" + action(d="読者・目的")))
        self.assertEqual(self.invoke("current").returncode, 1)
        result = subprocess.run([sys.executable, str(CHECK), "--root", str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("slug=current reason=quality", result.stdout)

    def test_claimed_deleted_design_is_not_legacy(self):
        design, history, _ = self.add_design_pair()
        design.unlink()
        marker = self.root / "wiki/insight/design-adoptions/current.json"
        marker.parent.mkdir(exist_ok=True)
        marker.write_text('{}')
        self.assertEqual(self.invoke("current").returncode, 1)
        result = subprocess.run([sys.executable, str(CHECK), "--root", str(self.root)], text=True, capture_output=True)
        self.assertIn("slug=current reason=deleted", result.stdout)

    def test_design_rubric_mismatch_is_error(self):
        self.add_design_pair()
        (self.root / "wiki/insight/references/design-quality-rubric.md").write_text("**design_rubric_version: 2**\n")
        self.assertEqual(self.invoke("current").returncode, 2)

    def test_unsupported_design_history_does_not_authorize_publication(self):
        _, history, article_eval = self.add_design_pair()
        future = history.with_name("20260102T000000Z-v2-design02.md")
        future.write_text(history.read_text().replace("rubric_version: 1", "rubric_version: 2")
                          .replace("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
                          .replace('run_id: "design01"', 'run_id: "design02"'))
        article_eval.write_text(article_eval.read_text().replace(str(history), str(future)))
        self.assertEqual(self.invoke("current").returncode, 1)

    def state_tool(self, *args):
        return subprocess.run([sys.executable, str(HERE / "evaluation_state.py"), *args],
                              cwd=self.root, text=True, capture_output=True)

    def claim_article(self, history):
        manifest = self.root / "manifest.json"
        init = self.state_tool("init", "--rubric-version", "6", "--manifest", str(manifest),
                              "--target", "current:wiki/insight/pages/current.md", "--design-evaluation", str(history))
        self.assertEqual(init.returncode, 0, init.stderr)
        result = self.state_tool("next", "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        return manifest

    def test_design_change_after_claim_rejects_article_save_and_resume_marks_it(self):
        design, history, article_eval = self.add_design_pair()
        manifest = self.claim_article(history)
        body = self.root / "body.md"
        body.write_text(article_eval.read_text().split("---\n", 2)[2])
        design.write_text(design.read_text() + "変更。\n")
        result = self.state_tool("save", "--manifest", str(manifest), "--slug", "current",
                                 "--body", str(body), "--design-evaluation", str(history))
        self.assertNotEqual(result.returncode, 0)
        resumed = self.state_tool("resume", "--manifest", str(manifest))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(json.loads(manifest.read_text())["items"][0]["error"], "design changed")

    def test_article_save_rejects_unclaimed_design_and_missing_outcome(self):
        _, history, article_eval = self.add_design_pair()
        body = self.root / "body.md"
        body.write_text(article_eval.read_text().split("---\n", 2)[2])
        manifest = self.root / "unclaimed.json"
        self.state_tool("init", "--rubric-version", "6", "--manifest", str(manifest),
                        "--target", "current:wiki/insight/pages/current.md")
        rejected = self.state_tool("next", "--manifest", str(manifest))
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(json.loads(manifest.read_text())["items"][0]["status"], "pending")
        result = self.state_tool("save", "--manifest", str(manifest), "--slug", "current",
                                 "--body", str(body), "--design-evaluation", str(history))
        self.assertNotEqual(result.returncode, 0)
        manifest = self.claim_article(history)
        body.write_text(body.read_text().replace("- D1:", "- D2:"))
        result = self.state_tool("save", "--manifest", str(manifest), "--slug", "current",
                                 "--body", str(body), "--design-evaluation", str(history))
        self.assertNotEqual(result.returncode, 0)

    def test_introduction_survives_without_evaluation_history(self):
        import shutil
        self.add_design_pair()
        marker = self.root / "wiki/insight/design-adoptions/current.json"
        marker.parent.mkdir(exist_ok=True)
        marker.write_text('{}')
        (self.root / "wiki/insight/designs/current.md").unlink()
        shutil.rmtree(self.root / "evaluations")
        manifest = self.root / "fresh.json"
        self.state_tool("init", "--rubric-version", "6", "--manifest", str(manifest),
                        "--target", "current:wiki/insight/pages/current.md")
        result = self.state_tool("next", "--manifest", str(manifest))
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run([sys.executable, str(CHECK), "--root", str(self.root)], text=True, capture_output=True)
        self.assertIn("slug=current reason=deleted", result.stdout)

    def test_design_claim_is_persistent_before_review(self):
        _, _, _ = self.add_design_pair()
        marker = self.root / "wiki/insight/design-adoptions/current.json"
        manifest = self.root / "design-manifest.json"
        result = self.state_tool("init", "--kind", "design", "--rubric-version", "1", "--manifest", str(manifest),
                                 "--target", "current:wiki/insight/designs/current.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.state_tool("next", "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(marker.read_text())["target"], "wiki/insight/designs/current.md")

    def invoke(self, slug: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(PUBLICATION), "--root", str(self.root), "--slug", slug], text=True, capture_output=True)

    def test_legacy_article_without_design_cannot_be_newly_published(self) -> None:
        result = self.invoke("current")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("INSIGHT_PUBLICATION DENY", result.stdout)

    def test_v3_history_is_legacy_and_cannot_allow_publication(self) -> None:
        from evaluation_state import latest_evaluations
        records, invalid = latest_evaluations(self.pages, self.root / "evaluations/insight")
        legacy = next(record for record in records if record["slug"] == "legacy")
        self.assertEqual(legacy["status"], "legacy")
        self.assertEqual(legacy["rubric_version"], 3)
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
        result = subprocess.run([sys.executable, str(CHECK), "--root", str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR:", result.stderr)


if __name__ == "__main__":
    unittest.main()
