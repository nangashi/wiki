"""Integration tests for registry-driven wiki structure tools."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
STRUCTURE = HERE / "wiki_structure.py"
LINT = HERE / "lint_check.py"


class WikiToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root / "wiki").mkdir()
        (self.root / "wiki/collections.toml").write_text("[collections]\na = 'a/wiki.toml'\nb = 'b/wiki.toml'\nc = 'c/wiki.toml'\n", encoding="utf-8")
        self.collection("a", "direct")
        self.collection("b", "checked")
        self.collection("c", "direct")
        self.page("a", "kept", "保持する概要。\n次の行。")
        self.page("a", "source", "[[kept]]\n[[b:target]]")
        self.page("b", "target", "対象ページ。")
        self.page("b", "rejected", "拒否されるページ。")
        self.page("b", "error", "hookがエラーになるページ。")
        self.page("c", "third", "第三のコレクション。")
        self.write("a/index.md", "# A\n\n## A\n\n- [[kept]] — 古い\n- [[gone]] — 消える\n")
        self.write("b/index.md", "# B\n\n")
        self.write("c/index.md", "# C\n\n- [[third]] — 古い\n")

    def tearDown(self) -> None: self.temp.cleanup()

    def write(self, relative: str, text: str) -> None:
        path = self.root / "wiki" / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")

    def collection(self, name: str, mode: str) -> None:
        publication = f"[publication]\nmode = '{mode}'\n"
        if mode == "checked": publication += "command = ['python3', 'hook.py']\n"
        self.write(f"{name}/wiki.toml", f"id = '{name}'\npurpose = '{name} purpose'\npages = 'pages'\nindex = 'index.md'\nschema = 'schema.md'\n[workflows]\ningest = 'workflows/ingest.md'\nreview = 'workflows/review.md'\nlint = 'workflows/lint.md'\n{publication}")
        self.write(f"{name}/schema.md", "# schema\n")
        self.write(f"{name}/workflows/lint.md", "# lint\n")
        self.write(f"{name}/workflows/ingest.md", "# ingest\n")
        self.write(f"{name}/workflows/review.md", "# review\n")
        (self.root / "wiki" / name / "pages").mkdir(parents=True, exist_ok=True)
        self.write("../hook.py", """import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser(); p.add_argument('--root'); p.add_argument('--slug'); a=p.parse_args()\nPath(a.root, 'hook-calls.txt').open('a').write(a.slug + '\\n')\nraise SystemExit({'rejected': 1, 'error': 7}.get(a.slug, 0))\n""")

    def page(self, collection: str, slug: str, overview: str) -> None:
        self.write(f"{collection}/pages/{slug}.md", f"---\ntitle: {slug}\n---\n\n# {slug}\n\n## 概要\n\n{overview}\n\n## 詳細\n\ntext\n")

    def invoke(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(script), *args, "--root", str(self.root)], text=True, capture_output=True, cwd=self.root)

    def test_registry_lists_arbitrary_collection_and_selected_index_isolated(self) -> None:
        listed = self.invoke(STRUCTURE, "collections")
        self.assertEqual(listed.returncode, 0, listed.stderr); self.assertIn("c\tc purpose", listed.stdout)
        before = (self.root / "wiki/c/index.md").read_text(encoding="utf-8")
        result = self.invoke(STRUCTURE, "index", "--collection", "a")
        self.assertEqual(result.returncode, 0, result.stderr)
        index = (self.root / "wiki/a/index.md").read_text(encoding="utf-8")
        self.assertIn("保持する概要。 次の行。", index); self.assertNotIn("gone", index)
        self.assertEqual((self.root / "wiki/c/index.md").read_text(encoding="utf-8"), before)

    def test_backlinks_cross_collection_and_fences(self) -> None:
        page = self.root / "wiki/a/pages/source.md"
        page.write_text(page.read_text(encoding="utf-8") + "\n```\n[[b:target]]\n```\n", encoding="utf-8")
        result = self.invoke(STRUCTURE, "backlinks", "b:target")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["a:source:10"])

    def test_checked_hook_denial_and_error_do_not_write_partial_index(self) -> None:
        before = (self.root / "wiki/b/index.md").read_text(encoding="utf-8")
        other_before = (self.root / "wiki/a/index.md").read_text(encoding="utf-8")
        denied = self.invoke(STRUCTURE, "index", "--add", "b:rejected")
        self.assertEqual(denied.returncode, 2); self.assertEqual((self.root / "wiki/b/index.md").read_text(encoding="utf-8"), before)
        self.assertEqual((self.root / "wiki/a/index.md").read_text(encoding="utf-8"), other_before)
        errored = self.invoke(STRUCTURE, "index", "--add", "b:error")
        self.assertEqual(errored.returncode, 2); self.assertEqual((self.root / "wiki/b/index.md").read_text(encoding="utf-8"), before)
        self.assertEqual((self.root / "wiki/a/index.md").read_text(encoding="utf-8"), other_before)

    def test_checked_hook_allows_new_page_and_selected_index_never_calls_other_hook(self) -> None:
        result = self.invoke(STRUCTURE, "index", "--collection", "a")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "hook-calls.txt").exists())
        result = self.invoke(STRUCTURE, "index", "--collection", "b", "--add", "b:target")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[[target]]", (self.root / "wiki/b/index.md").read_text(encoding="utf-8"))
        self.assertEqual((self.root / "hook-calls.txt").read_text(encoding="utf-8").splitlines(), ["target"])

    def test_duplicate_slug_is_reported_and_rejected_without_index_writes(self) -> None:
        self.page("c", "target", "第三の重複ページ。")
        before_a = (self.root / "wiki/a/index.md").read_text(encoding="utf-8")
        before_b = (self.root / "wiki/b/index.md").read_text(encoding="utf-8")
        lint = self.invoke(LINT, "--collection", "b")
        self.assertEqual(lint.returncode, 0, lint.stderr)
        self.assertIn("DUPLICATE_SLUG  collection=b  slug=target  collections=b,c", lint.stdout)
        rejected = self.invoke(STRUCTURE, "index", "--add", "b:target")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual((self.root / "wiki/a/index.md").read_text(encoding="utf-8"), before_a)
        self.assertEqual((self.root / "wiki/b/index.md").read_text(encoding="utf-8"), before_b)

    def test_existing_entry_does_not_run_checked_hook(self) -> None:
        self.write("b/index.md", "# B\n\n- [[rejected]] — 以前から公開済み\n")
        result = self.invoke(STRUCTURE, "index", "--collection", "b")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("拒否されるページ。", (self.root / "wiki/b/index.md").read_text(encoding="utf-8"))

    def test_lint_collection_selection_isolated(self) -> None:
        result = self.invoke(LINT, "--collection", "a")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("COLLECTIONS: a", result.stdout)
        self.assertNotIn("ref=b:target  type=cross", result.stdout)
        self.assertNotIn("collection=b", result.stdout)

    def test_empty_selected_collection_still_runs_configured_checks(self) -> None:
        page = self.root / "wiki/c/pages/third.md"; page.unlink()
        config = self.root / "wiki/c/wiki.toml"
        config.write_text(config.read_text(encoding="utf-8").replace("[publication]", "[checks]\ncommands = [[\"python3\", \"empty-check.py\"]]\n[publication]"), encoding="utf-8")
        (self.root / "empty-check.py").write_text("from pathlib import Path\nimport sys\nPath(sys.argv[-1], 'empty-check-ran').write_text('yes')\n", encoding="utf-8")
        result = self.invoke(LINT, "--collection", "c", "--checks")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("共通チェックをスキップ", result.stdout)
        self.assertTrue((self.root / "empty-check-ran").is_file())

    def test_invalid_or_incomplete_toml_configuration_fails(self) -> None:
        path = self.root / "wiki/a/wiki.toml"
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace("mode = 'direct'", "# mode omitted"), encoding="utf-8")
        self.assertEqual(self.invoke(STRUCTURE, "collections").returncode, 2)
        path.write_text(original.replace("[publication]", "checks = 'wrong'\n[publication]"), encoding="utf-8")
        self.assertEqual(self.invoke(STRUCTURE, "collections").returncode, 2)
        path.write_text(original.replace("purpose = 'a purpose'", 'purpose = """a\npurpose"""\nid = "duplicate"'), encoding="utf-8")
        self.assertEqual(self.invoke(STRUCTURE, "collections").returncode, 2)


if __name__ == "__main__": unittest.main()
