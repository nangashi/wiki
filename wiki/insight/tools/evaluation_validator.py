#!/usr/bin/env python3
"""Validate qualitative evaluations and read explicitly versioned legacy history."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DIMENSIONS = ("核心と推論力", "論理と構造", "有用性と適用境界", "事実基盤", "情報設計", "日本語の自然さ")
CURRENT_RUBRIC_VERSION = 5
ACTION_TYPES = ("修正必須", "調査必須", "任意改善")
REQUIRED_TYPES = ACTION_TYPES[:2]
SECTIONS = ("再利用性ゲート", "観点別評価", "対応項目", "良い点")
ACTION_FIELDS = ("種別", "観点", "対象箇所", "問題", "改善後に満たす条件", "対応方法")
RESEARCH_FIELDS = ("確認対象", "必要な理由", "調査先", "結果ごとの対応")


class ValidationError(ValueError):
    pass


def _body(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValidationError("frontmatterが閉じていません")
    return text[end + 5:]


def _version(text: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    if not text.startswith("---\n"):
        return CURRENT_RUBRIC_VERSION
    end = text.find("\n---\n", 4)
    versions = re.findall(r"(?m)^rubric_version: ([0-9]+)[ \t]*$", text[4:end])
    if end < 0 or len(versions) != 1:
        raise ValidationError("履歴のrubric_versionが不正です")
    return int(versions[0])


def _fields(text: str, names: tuple[str, ...], context: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- ([^:]+):[ \t]*(\S.*?)[ \t]*", line)
        if not match or match[1] not in names:
            raise ValidationError(f"{context}のフィールドが不正または空です: {line}")
        if match[1] in result:
            raise ValidationError(f"{context}の{match[1]}が重複しています")
        result[match[1]] = match[2]
    missing = set(names) - set(result)
    if missing:
        raise ValidationError(f"{context}に必須フィールドがありません: {', '.join(sorted(missing))}")
    return result


def _actions(section: str) -> list[dict]:
    if section.strip() == "- なし":
        return []
    headings = list(re.finditer(r"(?m)^### P([1-9][0-9]*):[ \t]*(\S.*?)[ \t]*$", section))
    if not headings or section[:headings[0].start()].strip():
        raise ValidationError("対応項目は『- なし』またはP1からの項目群にしてください")
    actions = []
    for index, heading in enumerate(headings, 1):
        if int(heading[1]) != index:
            raise ValidationError("対応項目IDはP1から連番にしてください")
        end = headings[index].start() if index < len(headings) else len(section)
        chunk = section[heading.end():end]
        types = re.findall(r"(?m)^- 種別:[ \t]*(\S.*?)[ \t]*$", chunk)
        if len(types) != 1 or types[0] not in ACTION_TYPES:
            raise ValidationError(f"P{index}の種別が不正です")
        names = ACTION_FIELDS + (RESEARCH_FIELDS if types[0] == "調査必須" else ())
        fields = _fields(chunk, names, f"P{index}")
        dimension = fields.pop("観点")
        if dimension not in DIMENSIONS + ("再利用性",):
            raise ValidationError(f"P{index}の観点が不正です")
        actions.append({"id": f"P{index}", "title": heading[2],
                        "type": fields.pop("種別"), "dimension": dimension, **fields})
    return actions


def _dimensions(section: str, gate: str) -> dict[str, dict]:
    rows = {}
    header_seen = False
    for line in section.splitlines():
        if not line.strip():
            continue
        if not line.startswith("|") or not line.rstrip().endswith("|"):
            raise ValidationError("観点別評価には表の行だけを記載してください")
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])]
        if cells == ["観点", "状態", "根拠"] and not header_seen:
            header_seen = True
            continue
        if len(cells) == 3 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if len(cells) != 3 or cells[0] not in DIMENSIONS:
            raise ValidationError(f"未定義または不正な観点行: {line}")
        name, state, reason = cells
        if name in rows:
            raise ValidationError(f"観点重複: {name}")
        allowed = {"対象外"} if gate == "不合格" else {"十分", "要対応"}
        if state not in allowed or not reason:
            raise ValidationError(f"{name}の状態または根拠が不正です")
        rows[name] = {"state": state, "reason": reason}
    if not header_seen:
        raise ValidationError("観点表のヘッダーがありません")
    if set(rows) != set(DIMENSIONS):
        raise ValidationError("観点別評価は定義済み6観点を各1行含める必要があります")
    return rows


def validate_text(text: str, expected_slug: str | None = None,
                  rubric_version: int | None = None) -> dict:
    slug = expected_slug or ""
    try:
        version = _version(text, rubric_version)
        if version in {1, 2}:
            from evaluation_validator_legacy import validate_text as legacy
            return legacy(text, expected_slug)
        # Versions 3, 4 and 5 intentionally share this qualitative body schema.
        # v3/v4 remain readable as persisted history; new runs use v5.
        if version not in {3, 4, CURRENT_RUBRIC_VERSION}:
            raise ValidationError(f"unsupported rubric_version: {version}")
        body = _body(text).strip() + "\n"
        headings = list(re.finditer(r"(?m)^## (.+?)[ \t]*$", body))
        if tuple(h[1] for h in headings) != SECTIONS:
            raise ValidationError("必須見出しは再利用性ゲート・観点別評価・対応項目・良い点の順で各1個です")
        head = body[:headings[0].start()].strip().splitlines()
        title = re.fullmatch(r"# Insight記事評価: ([a-z0-9][a-z0-9-]*)", head[0]) if head else None
        if not title:
            raise ValidationError("評価タイトルが不正です")
        slug = title[1]
        if expected_slug and expected_slug != slug:
            raise ValidationError(f"slug不一致: expected={expected_slug} actual={slug}")
        gate = _fields("\n".join(head[1:]), ("reusability_gate",), "サマリ")["reusability_gate"]
        if gate not in {"合格", "不合格"}:
            raise ValidationError("reusability_gateは合格/不合格のみです")
        sections = {h[1]: body[h.end():headings[i+1].start() if i+1 < len(headings) else len(body)]
                    for i, h in enumerate(headings)}
        _fields(sections["再利用性ゲート"], ("R1", "R2", "R3", "R4"), "再利用性ゲート")
        rows = _dimensions(sections["観点別評価"], gate)
        actions = _actions(sections["対応項目"])
        for action in actions:
            dimension = action["dimension"]
            if dimension == "再利用性":
                if gate != "不合格":
                    raise ValidationError("再利用性の対応項目はゲート不合格時のみです")
            elif action["type"] in REQUIRED_TYPES and rows[dimension]["state"] != "要対応":
                raise ValidationError(f"{action['id']}の必須対応は観点『{dimension}』を要対応にします")
        if gate == "不合格":
            if not any(a["type"] == "修正必須" and a["dimension"] == "再利用性" for a in actions):
                raise ValidationError("ゲート不合格には再利用性の修正必須対応が必要です")
        else:
            for dimension, row in rows.items():
                if row["state"] == "要対応" and not any(
                        a["dimension"] == dimension and a["type"] in REQUIRED_TYPES for a in actions):
                    raise ValidationError(f"{dimension}が要対応なら必須対応が必要です")
        strengths = [line for line in sections["良い点"].splitlines() if line.strip()]
        if not strengths or any(not re.fullmatch(r"- \S.*", line) for line in strengths):
            raise ValidationError("良い点には具体的な箇条書きが必要です")
        revision = sum(a["type"] == "修正必須" for a in actions)
        research = sum(a["type"] == "調査必須" for a in actions)
        optional = sum(a["type"] == "任意改善" for a in actions)
        passed = gate == "合格" and not revision and not research
        return {"valid": True, "errors": [], "slug": slug, "reusability_gate": gate,
                "pass": passed, "decision": "対象外" if gate == "不合格" else "公開可" if passed else "要対応",
                "revision_count": revision, "research_count": research, "optional_count": optional,
                "actions": actions, "dimensions": rows}
    except ValidationError as exc:
        return {"valid": False, "errors": [str(exc)], "slug": slug, "pass": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--slug")
    parser.add_argument("--rubric-version", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate_text(args.file.read_text(encoding="utf-8"), args.slug, args.rubric_version)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["valid"]:
        decision = result.get("decision", result.get("verdict", "legacy"))
        print(f"EVALUATION_VALID slug={result['slug']} decision={decision}")
    else:
        for error in result["errors"]:
            print(f"EVALUATION_INVALID: {error}", file=sys.stderr)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
