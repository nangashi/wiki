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
        (references / "article-quality-rubric.md").write_text("**rubric_version: 4**\n", encoding="utf-8")
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

    def write_evaluation(self, slug: str, rubric_version: int = 4) -> None:
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
            "---\n" + ev(), encoding="utf-8")
        # The shared fixture is fixed to slug=sample; make the persisted evaluation valid for this page.
        destination.write_text(destination.read_text(encoding="utf-8").replace("# Insight記事評価: sample", f"# Insight記事評価: {slug}"), encoding="utf-8")

    def invoke(self, slug: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(PUBLICATION), "--root", str(self.root), "--slug", slug], text=True, capture_output=True)

    def test_current_passing_evaluation_allows_publication(self) -> None:
        result = self.invoke("current")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("INSIGHT_PUBLICATION ALLOW", result.stdout)

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
