#!/usr/bin/env python3
"""Tests for verbatim extraction of subagent reports."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from extract_agent_report import extract  # noqa: E402


def assistant(*parts):
    return json.dumps({"type": "assistant", "message": {"content": list(parts)}}, ensure_ascii=False)


class ExtractTest(unittest.TestCase):
    def write(self, lines):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        tmp.write("\n".join(lines) + "\n")
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return Path(tmp.name)

    def test_latest_text_reply_wins_and_is_verbatim(self):
        path = self.write([
            json.dumps({"type": "user", "message": {"content": "# Insight記事評価: 依頼文の見本"}}, ensure_ascii=False),
            assistant({"type": "text", "text": "# Insight記事評価: old\n"}),
            "not json",
            assistant({"type": "text", "text": "  # Insight記事評価: new\n- R1: A & B <x>\n"}),
        ])
        self.assertEqual(extract(path, "# Insight記事評価:"), "# Insight記事評価: new\n- R1: A & B <x>\n")

    def test_handback_tool_payload_is_found(self):
        path = self.write([
            assistant({"type": "text", "text": "調べます"}),
            assistant({"type": "tool_use", "name": "SubagentHandback", "input": {"report": "- 概念と関係: a\n- 適用テスト: b"}}),
        ])
        self.assertEqual(extract(path, "- 概念と関係:"), "- 概念と関係: a\n- 適用テスト: b\n")

    def test_missing_report_fails_cli(self):
        path = self.write([assistant({"type": "text", "text": "no report"})])
        result = subprocess.run([sys.executable, str(HERE / "extract_agent_report.py"), str(path), "--marker", "# Insight設計評価:"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("REPORT_NOT_FOUND", result.stderr)


if __name__ == "__main__":
    unittest.main()
