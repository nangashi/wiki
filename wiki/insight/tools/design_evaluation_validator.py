#!/usr/bin/env python3
"""Validate the independent insight design-evaluation body (rubric v1)."""
from __future__ import annotations

import re
from evaluation_validator import (ACTION_FIELDS, ACTION_TYPES, REQUIRED_TYPES,
                                  RESEARCH_FIELDS, ValidationError, _actions,
                                  _body, _fields)

DIMENSIONS = ("読者・目的", "読後の到達点", "内容と順序", "主張と根拠・境界", "採用・省略")
CURRENT_RUBRIC_VERSION = 1
SECTIONS = ("再利用性ゲート", "観点別評価", "対応項目", "良い点")


def _design_actions(section: str) -> list[dict]:
    # Reuse the P-field grammar while constraining the dimension vocabulary.
    actions = _actions(section, DIMENSIONS)
    for action in actions:
        if action["dimension"] not in DIMENSIONS + ("再利用性",):
            raise ValidationError(f"{action['id']}の観点が設計rubricにありません")
    return actions


def _dimensions(section: str, gate: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}; header = False
    for line in section.splitlines():
        if not line.strip(): continue
        if not line.startswith("|") or not line.rstrip().endswith("|"):
            raise ValidationError("観点別評価には表の行だけを記載してください")
        cells = [x.strip() for x in line.strip()[1:-1].split("|")]
        if cells == ["観点", "状態", "根拠"] and not header: header = True; continue
        if len(cells) == 3 and all(re.fullmatch(r":?-{3,}:?", x) for x in cells): continue
        if len(cells) != 3 or cells[0] not in DIMENSIONS or cells[0] in rows:
            raise ValidationError(f"未定義または重複した設計観点: {line}")
        if cells[1] not in ({"対象外"} if gate == "不合格" else {"十分", "要対応"}) or not cells[2]:
            raise ValidationError(f"{cells[0]}の状態または根拠が不正です")
        rows[cells[0]] = {"state": cells[1], "reason": cells[2]}
    if not header or set(rows) != set(DIMENSIONS):
        raise ValidationError("観点表は設計の5観点を各1行含める必要があります")
    return rows


def validate_text(text: str, expected_slug: str | None = None, rubric_version: int | None = None) -> dict:
    slug = expected_slug or ""
    try:
        if rubric_version not in (None, 1): raise ValidationError("unsupported design rubric_version")
        body = _body(text).strip() + "\n"; headings = list(re.finditer(r"(?m)^## (.+?)[ \t]*$", body))
        if tuple(h[1] for h in headings) != SECTIONS: raise ValidationError("設計評価の必須見出しが不正です")
        head = body[:headings[0].start()].strip().splitlines()
        title = re.fullmatch(r"# Insight設計評価: ([a-z0-9][a-z0-9-]*)", head[0]) if head else None
        if not title: raise ValidationError("設計評価タイトルが不正です")
        slug = title[1]
        if expected_slug and slug != expected_slug: raise ValidationError(f"slug不一致: expected={expected_slug} actual={slug}")
        gate = _fields("\n".join(head[1:]), ("reusability_gate",), "サマリ")["reusability_gate"]
        if gate not in {"合格", "不合格"}: raise ValidationError("reusability_gateは合格/不合格のみです")
        sections = {h[1]: body[h.end():headings[i + 1].start() if i + 1 < len(headings) else len(body)] for i,h in enumerate(headings)}
        _fields(sections["再利用性ゲート"], ("R1", "R2", "R3", "R4"), "再利用性ゲート")
        rows = _dimensions(sections["観点別評価"], gate); actions = _design_actions(sections["対応項目"])
        for action in actions:
            if action["dimension"] == "再利用性":
                if gate != "不合格": raise ValidationError("再利用性の対応項目はゲート不合格時のみです")
            elif action["type"] in REQUIRED_TYPES and rows[action["dimension"]]["state"] != "要対応":
                raise ValidationError(f"{action['id']}の必須対応と観点状態が不整合です")
        if gate == "不合格" and not any(a["type"] == "修正必須" and a["dimension"] == "再利用性" for a in actions):
            raise ValidationError("ゲート不合格には再利用性の修正必須対応が必要です")
        if gate == "合格":
            for name,row in rows.items():
                if row["state"] == "要対応" and not any(a["dimension"] == name and a["type"] in REQUIRED_TYPES for a in actions):
                    raise ValidationError(f"{name}が要対応なら必須対応が必要です")
        if not any(re.fullmatch(r"- \S.*", x) for x in sections["良い点"].splitlines() if x.strip()): raise ValidationError("良い点が必要です")
        revision=sum(a["type"]=="修正必須" for a in actions); research=sum(a["type"]=="調査必須" for a in actions)
        passed=gate=="合格" and not revision and not research
        return {"valid":True,"errors":[],"slug":slug,"reusability_gate":gate,"pass":passed,"decision":"対象外" if gate=="不合格" else "公開可" if passed else "要対応","revision_count":revision,"research_count":research,"optional_count":sum(a["type"]=="任意改善" for a in actions),"actions":actions,"dimensions":rows}
    except ValidationError as exc:
        return {"valid":False,"errors":[str(exc)],"slug":slug,"pass":False}
