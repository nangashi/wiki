#!/usr/bin/env python3
"""Print a subagent's final report verbatim from its transcript (JSONL).

Evaluator replies must be saved without retyping.  The report is either the
subagent's last text reply or the payload of its hand-back tool call; the
latest one containing ``--marker`` (for example ``# Insight記事評価:`` or
``- 概念と関係:``) wins.  Nothing is rewritten, trimmed inside, or unescaped.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract(path: Path, marker: str) -> str | None:
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("type") != "assistant":
            continue
        for part in record.get("message", {}).get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text" and marker in part.get("text", ""):
                found = part["text"]
            elif part.get("type") == "tool_use":
                for value in (part.get("input") or {}).values():
                    if isinstance(value, str) and marker in value:
                        found = value
    return found.strip() + "\n" if found else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path, help="subagent transcript, e.g. .../subagents/agent-<id>.jsonl")
    parser.add_argument("--marker", required=True, help="text the report must contain")
    args = parser.parse_args()
    report = extract(args.transcript, args.marker)
    if report is None:
        print(f"REPORT_NOT_FOUND marker={args.marker!r} transcript={args.transcript}", file=sys.stderr)
        return 1
    sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
