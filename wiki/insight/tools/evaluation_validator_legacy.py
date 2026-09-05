#!/usr/bin/env python3
"""Validate the complete Codex insight-evaluation body.

This module is deliberately independent from ``codex exec``.  It is used by
ingest, review-page, lint and the batch state helper before an evaluation may
be saved or counted as CURRENT.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DIMENSIONS = {
    "核心と推論力": 25,
    "論理と構造": 20,
    "有用性と適用境界": 15,
    "事実基盤": 15,
    "情報設計": 10,
    "日本語の自然さ": 15,
}
VERDICTS = {
    range(90, 101): "公開品質",
    range(80, 90): "良好。軽微な改善のみ",
    range(70, 80): "利用可能だが改善対象",
    range(60, 70): "主要な修正が必要",
    range(0, 60): "構造的な書き直しが必要",
}
REQUIRED_SECTIONS = ["再利用性ゲート", "点数内訳", "Blocking", "Major", "Minor", "改善項目", "良い点"]
SUMMARY_KEYS = ["reusability_gate", "raw_score", "score_cap", "final_score", "verdict", "pass"]
IMPROVEMENT_FIELDS = ["対象箇所", "問題", "改善後に満たす条件", "改善方法", "要外部調査"]


class ValidationError(ValueError):
    pass


def _body(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError("frontmatterが閉じていません")
    return text[end + 5 :]


def _section(body: str, name: str) -> str:
    matches = list(re.finditer(rf"(?m)^## {re.escape(name)}\s*$", body))
    if len(matches) != 1:
        raise ValidationError(f"見出し『{name}』は1個必要です")
    start = matches[0].end()
    nxt = re.search(r"(?m)^## ", body[start:])
    return body[start : start + nxt.start() if nxt else len(body)]


def _summary(body: str) -> dict[str, str]:
    first_section = re.search(r"(?m)^## ", body)
    head = body[: first_section.start()] if first_section else body
    result: dict[str, str] = {}
    for key in SUMMARY_KEYS:
        values = re.findall(rf"(?m)^- {key}:\s*(.+?)\s*$", head)
        if len(values) != 1:
            raise ValidationError(f"summaryの{key}は1個必要です")
        result[key] = values[0]
    return result


def _issues(section: str, severity: str) -> list[str]:
    items = [m.strip() for m in re.findall(r"(?m)^- (.+?)\s*$", section)]
    if not items:
        raise ValidationError(f"{severity}には箇条書きが必要です")
    if "なし" in items and (len(items) != 1 or items[0] != "なし"):
        raise ValidationError(f"{severity}の『なし』と問題項目は併記できません")
    return [] if items == ["なし"] else items


def _verdict(score: int) -> str:
    return next(label for band, label in VERDICTS.items() if score in band)


def validate_text(text: str, expected_slug: str | None = None) -> dict:
    errors: list[str] = []
    try:
        body = _body(text).strip() + "\n"
        title = re.findall(r"(?m)^# Insight記事評価: ([a-z0-9][a-z0-9-]*)\s*$", body)
        if len(title) != 1:
            raise ValidationError("評価タイトルは1個必要です")
        slug = title[0]
        if expected_slug and slug != expected_slug:
            errors.append(f"slug不一致: expected={expected_slug} actual={slug}")

        for heading in REQUIRED_SECTIONS:
            _section(body, heading)
        summary = _summary(body)
        if summary["reusability_gate"] not in {"合格", "不合格"}:
            errors.append("reusability_gateは合格/不合格のみです")

        gate_section = _section(body, "再利用性ゲート")
        for rule in ("R1", "R2", "R3", "R4"):
            values = re.findall(rf"(?m)^- {rule}:\s*(.+?)\s*$", gate_section)
            if len(values) != 1 or not values[0].strip():
                errors.append(f"再利用性ゲートの{rule}根拠は1個必要です")

        table = _section(body, "点数内訳")
        rows: dict[str, tuple[str, str, int, str]] = {}
        for line in table.splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5 or cells[0] not in DIMENSIONS:
                continue
            if cells[0] in rows:
                errors.append(f"観点重複: {cells[0]}")
            rows[cells[0]] = (cells[1], cells[2], int(cells[3]) if cells[3].isdigit() else -1, cells[4])
        if set(rows) != set(DIMENSIONS):
            errors.append("点数内訳は定義済み6観点を各1行含める必要があります")

        blocking = _issues(_section(body, "Blocking"), "Blocking")
        major = _issues(_section(body, "Major"), "Major")
        _issues(_section(body, "Minor"), "Minor")

        gate_pass = summary["reusability_gate"] == "合格"
        ratings: list[int] = []
        converted: list[int] = []
        if set(rows) == set(DIMENSIONS):
            for name, maximum in DIMENSIONS.items():
                rating_s, score_s, allocation, reason = rows[name]
                if allocation != maximum:
                    errors.append(f"{name}の配点は{maximum}である必要があります")
                if not reason:
                    errors.append(f"{name}の根拠がありません")
                if gate_pass:
                    if not rating_s.isdigit() or int(rating_s) not in range(6):
                        errors.append(f"{name}の0〜5評価が不正です")
                        continue
                    rating = int(rating_s)
                    expected = rating * maximum // 5
                    if not score_s.isdigit() or int(score_s) != expected:
                        errors.append(f"{name}の換算点不一致: expected={expected} actual={score_s}")
                    ratings.append(rating)
                    converted.append(expected)
                elif rating_s != "採点対象外" or score_s != "採点対象外":
                    errors.append(f"ゲート不合格時の{name}は採点対象外にしてください")

        raw: int | None = None
        cap: int | None = None
        final: int | None = None
        if gate_pass:
            for key in ("raw_score", "final_score"):
                if not summary[key].isdigit() or not 0 <= int(summary[key]) <= 100:
                    errors.append(f"{key}は0〜100の整数である必要があります")
            if summary["raw_score"].isdigit():
                raw = int(summary["raw_score"])
                if len(converted) == 6 and raw != sum(converted):
                    errors.append(f"raw_score不一致: expected={sum(converted)} actual={raw}")
            if summary["score_cap"] not in {"なし", "49", "59"}:
                errors.append("score_capはなし/49/59のみです")
            else:
                cap = None if summary["score_cap"] == "なし" else int(summary["score_cap"])
            if summary["final_score"].isdigit():
                final = int(summary["final_score"])
                if raw is not None and final != min(raw, cap if cap is not None else 100):
                    errors.append("final_scoreはmin(raw_score, score_cap)と一致しません")
                if summary["verdict"] != _verdict(final):
                    errors.append("verdictがfinal_scoreの品質区分と一致しません")
            if cap is None and blocking:
                errors.append("Blockingがある評価のscore_capを『なし』にはできません")
            if cap is not None and not blocking:
                errors.append("score_capがある評価にはBlocking根拠が必要です")
            if len(ratings) == 6 and ratings[0] < 2 and cap != 49:
                errors.append("核心と推論力が2/5未満ならscore_capは49です")
            expected_pass = bool(raw is not None and raw >= 80 and len(ratings) == 6 and min(ratings) >= 3 and not blocking and not major)
            if summary["pass"] != ("はい" if expected_pass else "いいえ"):
                errors.append("passが合格条件と矛盾します")
        else:
            for key in ("raw_score", "score_cap", "final_score", "verdict"):
                if summary[key] != "採点対象外":
                    errors.append(f"ゲート不合格時の{key}は採点対象外である必要があります")
            if summary["pass"] != "いいえ":
                errors.append("ゲート不合格時のpassは『いいえ』です")
            if not blocking:
                errors.append("ゲート不合格にはBlocking根拠が必要です")

        improvements = _section(body, "改善項目")
        if re.fullmatch(r"\s*- なし\s*", improvements):
            if blocking or major or summary["pass"] == "いいえ":
                errors.append("不合格またはBlocking/Majorありでは改善項目が必要です")
            priorities: list[str] = []
        else:
            blocks = list(re.finditer(r"(?m)^### P([1-9][0-9]*):\s*(\S.*)$", improvements))
            priorities = [m.group(1) for m in blocks]
            if not blocks:
                errors.append("改善項目はP1から始めるか『- なし』にしてください")
            if priorities != [str(i) for i in range(1, len(priorities) + 1)]:
                errors.append("改善項目IDはP1から連番にしてください")
            for idx, match in enumerate(blocks):
                chunk = improvements[match.end() : blocks[idx + 1].start() if idx + 1 < len(blocks) else len(improvements)]
                for field in IMPROVEMENT_FIELDS:
                    values = re.findall(rf"(?m)^- {re.escape(field)}:\s*(.+?)\s*$", chunk)
                    if len(values) != 1 or not values[0].strip():
                        errors.append(f"P{match.group(1)}の{field}は1個必要です")
                    if field == "要外部調査" and values and values[0] not in {"はい", "いいえ"}:
                        errors.append(f"P{match.group(1)}の要外部調査ははい/いいえのみです")

        good = _section(body, "良い点")
        if not re.search(r"(?m)^- \S", good):
            errors.append("良い点には具体的な箇条書きが必要です")
    except (ValidationError, ValueError) as exc:
        errors.append(str(exc))
        slug = expected_slug or ""
        summary = {}
        blocking = []
        major = []
        ratings = []
        raw = cap = final = None

    return {
        "valid": not errors,
        "errors": errors,
        "slug": slug,
        "reusability_gate": summary.get("reusability_gate"),
        "raw_score": raw,
        "score_cap": cap,
        "final_score": final,
        "verdict": summary.get("verdict"),
        "pass": summary.get("pass") == "はい",
        "blocking_count": len(blocking),
        "blocking_issues": blocking,
        "major_count": len(major),
        "minimum_rating": min(ratings) if ratings else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--slug")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate_text(args.file.read_text(encoding="utf-8"), args.slug)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["valid"]:
        print(f"EVALUATION_VALID slug={result['slug']} final_score={result['final_score'] if result['final_score'] is not None else 'na'}")
    else:
        for error in result["errors"]:
            print(f"EVALUATION_INVALID: {error}", file=sys.stderr)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
