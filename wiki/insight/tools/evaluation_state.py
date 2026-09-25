#!/usr/bin/env python3
"""State and persistence helper for insight evaluations.

The helper never launches evaluators.  The main agent owns process creation;
this module only prepares/claims work, validates results, adds trusted
metadata, saves the final evaluation, appends external verification evidence,
resumes interrupted runs, and rebuilds the quality queue.

Each slug keeps exactly one current article evaluation and one current design
evaluation (``wiki/insight/evaluations/<slug>/{article,design}.md``); every
save overwrites them and git keeps the history.  Run manifests and
intermediate outputs live under the git-ignored ``.cache/insight-runs/``.
"""

from __future__ import annotations

import argparse
import datetime as dt

import json
import re
import secrets
import subprocess
import sys
from pathlib import Path

from evaluation_validator import CURRENT_RUBRIC_VERSION, validate_text
from design_evaluation_validator import CURRENT_RUBRIC_VERSION as DESIGN_RUBRIC_VERSION
from design_evaluation_validator import validate_text as validate_design_text
from insight_source_validator import validate as validate_sources

MAX_BATCH = 3
MAX_ATTEMPTS = 3  # initial attempt plus two clean retries
# Evaluator recorded on new saves; must match .claude/agents/evaluator.md.
CURRENT_EVALUATOR = ("claude", "opus")
ACCEPTED_EVALUATORS = {CURRENT_EVALUATOR}
EVALUATIONS_ROOT = Path("wiki/insight/evaluations")
EVIDENCE_ROOT = Path("wiki/insight/evidence")
BLOB = r"[0-9a-f]{40}(?:[0-9a-f]{24})?"
EVIDENCE_SECTIONS = ("確認済み", "未確認", "誤り")


def current_rubric_version(pages_dir: Path) -> int:
    """Read the canonical insight rubric beside the page tree."""
    for parent in (pages_dir, *pages_dir.parents):
        candidate = parent / "references" / "article-quality-rubric.md"
        if candidate.is_file():
            match = re.search(r"rubric_version:\s*([0-9]+)", candidate.read_text(encoding="utf-8"))
            if not match:
                raise ValueError(f"rubric_version is missing from {candidate}")
            version = int(match.group(1))
            if version != CURRENT_RUBRIC_VERSION:
                raise ValueError(f"unsupported rubric_version: {version}")
            return version
    raise ValueError("canonical article-quality-rubric.md was not found")


def current_design_rubric_version(designs_dir: Path) -> int:
    for parent in (designs_dir, *designs_dir.parents):
        candidate = parent / "references" / "design-quality-rubric.md"
        if candidate.is_file():
            match = re.search(r"rubric_version:\s*([0-9]+)", candidate.read_text(encoding="utf-8"))
            if not match: raise ValueError(f"rubric_version is missing from {candidate}")
            version = int(match.group(1))
            if version != DESIGN_RUBRIC_VERSION: raise ValueError(f"unsupported design rubric_version: {version}")
            return version
    raise ValueError("canonical design-quality-rubric.md was not found")


def design_outcome_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    names = ("読者・目的", "読後の到達点", "内容と順序", "主張と根拠・境界", "採用・省略")
    headings = list(re.finditer(r"(?m)^## (.+)$", text))
    if tuple(h[1] for h in headings) != names:
        raise ValueError("design must contain its five canonical sections in order")
    sections = {h[1]: text[h.end():headings[i+1].start() if i+1 < len(headings) else len(text)].strip()
                for i, h in enumerate(headings)}
    if not all(sections.values()): raise ValueError("design sections must not be empty")
    ids = re.findall(r"(?m)^- (D[1-9][0-9]*): \S.*$", sections["読後の到達点"])
    if not ids or len(ids) != len(set(ids)): raise ValueError("design requires unique D outcome IDs")
    return set(ids)


def design_application_test(path: Path) -> str:
    """Return the situation half of the design's single application test (given to stage 1)."""
    lines = re.findall(r"(?m)^- 適用テスト: (.+)$", path.read_text(encoding="utf-8"))
    if len(lines) != 1 or "→" not in lines[0]:
        raise ValueError("design requires exactly one '- 適用テスト: 状況 → 期待する推論' line")
    situation = lines[0].split("→", 1)[0].strip()
    if not situation: raise ValueError("design application test has an empty situation")
    return situation


def kind_version(kind: str) -> int:
    return DESIGN_RUBRIC_VERSION if kind == "design" else CURRENT_RUBRIC_VERSION


def target_path(kind: str, slug: str) -> str:
    return f"wiki/insight/{'designs' if kind == 'design' else 'pages'}/{slug}.md"


def evaluation_path(root: Path, slug: str, kind: str = "article") -> Path:
    return root / slug / ("design.md" if kind == "design" else "article.md")


def design_file_for(target: Path, slug: str) -> Path:
    return target.parent.parent / "designs" / f"{slug}.md"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def render_manifest(data: dict) -> str:
    lines = [
        f"# Insight evaluation run: {data['run_id']}", "",
        f"- kind: {data.get('kind', 'article')}",
        f"- rubric_version: {data['rubric_version']}",
        f"- started_at: {data['started_at']}",
        f"- updated_at: {data['updated_at']}",
        "", "| slug | target | status | attempts | evaluation | error |",
        "|---|---|---|---:|---|---|",
    ]
    for item in data["items"]:
        lines.append("| {slug} | {target} | {status} | {attempts} | {evaluation} | {error} |".format(
            slug=item["slug"], target=item["target"], status=item["status"],
            attempts=item["attempts"], evaluation=item.get("evaluation", ""),
            error=item.get("error", "").replace("|", "\\|")))
    return "\n".join(lines) + "\n"


def save_manifest(path: Path, data: dict) -> None:
    data["updated_at"] = now()
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    atomic_write(path.with_suffix(".md"), render_manifest(data))


def git_blob(path: Path) -> str:
    result = subprocess.run(["git", "hash-object", str(path)], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def read_frontmatter(text: str) -> dict | None:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    lines = match.group(1).splitlines()
    pairs = [re.fullmatch(r'([a-z_]+): (?:"([^"]*)"|([0-9]+))', line) for line in lines]
    if not all(pairs):
        return None
    meta = {m[1]: m[2] if m[2] is not None else m[3] for m in pairs}
    return meta if len(meta) == len(lines) else None


def frontmatter_version(path: Path) -> int | None:
    meta = read_frontmatter(path.read_text(encoding="utf-8"))
    value = (meta or {}).get("rubric_version", "")
    return int(value) if value.isdigit() else None


def parse_metadata(path: Path, expected_slug: str, kind: str = "article") -> dict | None:
    """Strictly parse a current-version evaluation file's trusted metadata."""
    if path.name != ("design.md" if kind == "design" else "article.md"):
        return None
    return parse_metadata_text(path.read_text(encoding="utf-8"), expected_slug, kind)


def parse_metadata_text(text: str, expected_slug: str, kind: str = "article") -> dict | None:
    meta = read_frontmatter(text)
    if meta is None:
        return None
    required = {"target", "target_blob", "rubric_version", "evaluator", "evaluator_model", "evaluated_at", "run_id", "round"}
    if kind == "article":
        required |= {"design_target", "design_blob", "design_evaluation_blob"}
    if set(meta) != required or meta["rubric_version"] != str(kind_version(kind)):
        return None
    if meta["target"] != target_path(kind, expected_slug):
        return None
    if (meta["evaluator"], meta["evaluator_model"]) not in ACCEPTED_EVALUATORS:
        return None
    blobs = ["target_blob"] + (["design_blob", "design_evaluation_blob"] if kind == "article" else [])
    if not all(re.fullmatch(BLOB, meta[key]) for key in blobs):
        return None
    if kind == "article" and meta["design_target"] != target_path("design", expected_slug):
        return None
    if not re.fullmatch(r"[a-z0-9]{8,32}", meta["run_id"]) or not re.fullmatch(r"[1-9][0-9]*", meta["round"]):
        return None
    try:
        dt.datetime.strptime(meta["evaluated_at"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return meta


def current_design_evaluation(evaluations_root: Path, slug: str) -> tuple[Path, dict] | None:
    """Return the slug's design evaluation if it has current metadata and a valid body."""
    path = evaluation_path(evaluations_root, slug, "design")
    if not path.is_file():
        return None
    meta = parse_metadata(path, slug, "design")
    if meta is None or not validate_design_text(path.read_text(encoding="utf-8"), slug, DESIGN_RUBRIC_VERSION)["valid"]:
        return None
    return path, meta


def cmd_init(args: argparse.Namespace) -> int:
    if args.rubric_version != kind_version(args.kind):
        raise SystemExit(f"new {args.kind} evaluation runs require rubric_version={kind_version(args.kind)}")
    targets: list[tuple[str, str]] = []
    for spec in args.target:
        slug, sep, path = spec.partition(":")
        if not sep or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise SystemExit(f"invalid --target: {spec}")
        targets.append((slug, path))
    directory = args.designs_dir if args.kind == "design" else args.pages_dir
    if directory:
        targets.extend((p.stem, target_path(args.kind, p.stem)) for p in Path(directory).glob("*.md"))
    unique = dict(sorted(set(targets)))
    if not unique:
        raise SystemExit("at least one --target or --pages-dir is required")
    claims = {}
    if args.kind == "article":
        missing = []
        for slug, target in unique.items():
            found = current_design_evaluation(args.evaluations_root, slug)
            if found is None:
                missing.append(slug); continue
            path, meta = found
            try: design_application_test(design_file_for(Path(target), slug))
            except (OSError, ValueError) as error: raise SystemExit(f"{slug}: {error}")
            claims[slug] = {"design_blob": meta["target_blob"], "design_evaluation": path.as_posix(),
                            "design_evaluation_blob": git_blob(path), "design_rubric_version": DESIGN_RUBRIC_VERSION}
        if missing:
            raise SystemExit(f"article evaluation runs require a current design rubric_version={DESIGN_RUBRIC_VERSION} "
                             f"evaluation at {args.evaluations_root}/<slug>/design.md: " + ", ".join(missing))
    data = {
        "schema_version": 3, "kind": args.kind, "run_id": args.run_id or secrets.token_hex(6),
        "rubric_version": args.rubric_version, "started_at": now(), "updated_at": now(),
        "items": [{"slug": slug, "target": target, "status": "pending", "attempts": 0,
                   "target_blob": "", "evaluation": "", "error": "", **claims.get(slug, {})} for slug, target in unique.items()],
    }
    save_manifest(args.manifest, data)
    print(f"RUN_INITIALIZED run_id={data['run_id']} total={len(data['items'])} manifest={args.manifest}")
    return 0


def design_claim_changed(item: dict) -> bool:
    if not all(item.get(k) for k in ("design_blob", "design_evaluation", "design_evaluation_blob", "design_rubric_version")):
        raise SystemExit("article claim requires its design evaluation")
    design_path = design_file_for(Path(item["target"]), item["slug"])
    current_design_rubric_version(design_path.parent)
    evaluation = Path(item["design_evaluation"])
    return (not design_path.is_file() or git_blob(design_path) != item["design_blob"]
            or not evaluation.is_file() or git_blob(evaluation) != item["design_evaluation_blob"])


def canonical_version(kind: str, target: Path) -> int:
    return current_design_rubric_version(target.parent) if kind == "design" else current_rubric_version(target.parent)


def cmd_next(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    kind = data.get("kind", "article")
    if data.get("rubric_version") != kind_version(kind):
        raise SystemExit(f"obsolete evaluation run cannot be resumed; initialize a v{kind_version(kind)} run")
    candidates = [i for i in data["items"] if i["status"] in {"pending", "retry"}]
    selected = candidates[: min(args.limit, MAX_BATCH)]
    for item in selected:
        if canonical_version(kind, Path(item["target"])) != data["rubric_version"]:
            raise SystemExit("canonical rubric changed; initialize a new run")
        git_blob(Path(item["target"]))
        if kind == "article" and design_claim_changed(item):
            raise SystemExit("design changed before article evaluation claim")
        if kind == "design": design_outcome_ids(Path(item["target"]))
    for item in selected:
        item["target_blob"] = git_blob(Path(item["target"]))
        item["status"] = "running"
        item["attempts"] += 1
        item["error"] = ""
    save_manifest(args.manifest, data)
    for item in selected:
        print(f"EVALUATION_NEXT slug={item['slug']} target={item['target']} attempt={item['attempts']}")
    if not selected:
        print("EVALUATION_NEXT none")
    return 0


def item_for(data: dict, slug: str) -> dict:
    found = [item for item in data["items"] if item["slug"] == slug]
    if len(found) != 1:
        raise SystemExit(f"unknown slug: {slug}")
    return found[0]


def cmd_fail(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    item = item_for(data, args.slug)
    if item["status"] != "running":
        raise SystemExit(f"{args.slug} is not running")
    item["status"] = "retry" if item["attempts"] < MAX_ATTEMPTS else "failed"
    item["error"] = args.error
    save_manifest(args.manifest, data)
    print(f"EVALUATION_{item['status'].upper()} slug={args.slug} attempts={item['attempts']}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    kind = data.get("kind", "article")
    if data.get("rubric_version") != kind_version(kind):
        raise SystemExit(f"obsolete evaluation run cannot be resumed; initialize a v{kind_version(kind)} run")
    count = 0
    for item in data["items"]:
        if canonical_version(kind, Path(item["target"])) != data["rubric_version"]:
            raise SystemExit("canonical rubric changed; initialize a new run")
        if kind == "article" and design_claim_changed(item):
            item["status"] = "pending"; item["target_blob"] = ""; item["error"] = "design changed"; count += 1; continue
        if item["status"] == "running":
            item["status"] = "retry" if item["attempts"] < MAX_ATTEMPTS else "failed"
            item["error"] = item.get("error") or "interrupted"
            count += 1
    save_manifest(args.manifest, data)
    print(f"RUN_RESUMED reset_running={count}")
    return 0


def stage1_mismatch(stage1: str, body: str) -> str:
    """Return an error unless the body's 記事単独読解 section equals the saved first-stage answer."""
    parts = re.split(r"^## 記事単独読解[ \t]*$", body, maxsplit=1, flags=re.M)
    if len(parts) != 2:
        return "記事単独読解の節がありません"
    section = re.split(r"^## ", parts[1], maxsplit=1, flags=re.M)[0]
    lines = lambda text: [line.strip() for line in text.splitlines() if line.strip()]
    if lines(section) != lines(stage1):
        return "記事単独読解が第一段階の保存済み回答と一致しません"
    return ""


def cmd_save(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    kind = data.get("kind", "article")
    if data.get("rubric_version") != kind_version(kind):
        raise SystemExit(f"obsolete evaluation run cannot save into v{kind_version(kind)} evaluations")
    item = item_for(data, args.slug)
    if item["status"] != "running":
        raise SystemExit(f"{args.slug} is not running")
    if args.round < 1:
        raise SystemExit("--round must be 1 or greater")
    raw = args.body.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        print("評価本文にfrontmatterを含めることはできません", file=sys.stderr)
        return 1
    validator = validate_design_text if kind == "design" else validate_text
    result = validator(raw, args.slug, kind_version(kind))
    if not result["valid"]:
        print("; ".join(result["errors"]), file=sys.stderr)
        return 1
    if kind == "article":
        if not args.stage1:
            raise SystemExit("article save requires --stage1 (the saved 記事単独読解 answer)")
        mismatch = stage1_mismatch(args.stage1.read_text(encoding="utf-8"), raw)
        if mismatch:
            print(mismatch, file=sys.stderr)
            return 1
    target = Path(item["target"])
    if canonical_version(kind, target) != data["rubric_version"]:
        raise SystemExit("canonical rubric changed since claim")
    source_diagnostics = validate_sources(target) if kind == "article" else []
    structural = [d for d in source_diagnostics if d.category == "structure"]
    quality = [d for d in source_diagnostics if d.category == "quality"]
    if structural:
        for diagnostic in structural:
            print(f"{diagnostic.code}: {diagnostic.reason}", file=sys.stderr)
        print("target article has structurally invalid external sources", file=sys.stderr)
        return 1
    if quality:
        required = [a for a in result["actions"] if a["type"] in {"修正必須", "調査必須"}]
        allowed_dimensions = {"事実基盤"} if result.get("reusability_gate") != "不合格" else {"再利用性"}
        source_action = all(any(a["dimension"] in allowed_dimensions and re.search(rf"(?<![A-Za-z0-9_]){re.escape(d.code)}(?![A-Za-z0-9_])", a.get("問題", "")) for a in required) for d in quality)
        if result.get("pass") or not source_action:
            for diagnostic in quality:
                print(f"{diagnostic.code}: {diagnostic.reason}", file=sys.stderr)
            print("source quality issue requires a matching mandatory 事実基盤 action and pass=いいえ", file=sys.stderr)
            return 1
    before = item.get("target_blob")
    if not before:
        raise SystemExit("evaluation was not claimed with next")
    if git_blob(target) != before:
        raise SystemExit("target changed since evaluation was claimed")
    timestamp = args.evaluated_at or now()
    run_id = args.evaluation_run_id or secrets.token_hex(6)
    if not re.fullmatch(r"[a-z0-9]{8,32}", run_id):
        raise SystemExit("evaluation run_id must be 8-32 lowercase alphanumerics")
    destination = evaluation_path(args.evaluations_root, args.slug, kind)
    design_meta = ""
    if kind == "article":
        if design_claim_changed(item):
            raise SystemExit("design or its evaluation changed since claim")
        design_target = design_file_for(target, args.slug)
        design_ids = design_outcome_ids(design_target)
        alignment_ids = set(re.findall(r"(?m)^- (D[1-9][0-9]*): \S", raw))
        if alignment_ids != design_ids:
            raise SystemExit("article design alignment must cover every current D ID exactly")
        if result.get("design_alignment") not in {"合格", "不合格"}:
            raise SystemExit("article evaluation requires design_alignment 合格 or 不合格")
        design_meta = (f'design_target: "{target_path("design", args.slug)}"\n'
                       f'design_blob: "{item["design_blob"]}"\n'
                       f'design_evaluation_blob: "{item["design_evaluation_blob"]}"\n')
    else:
        design_outcome_ids(target)
    frontmatter = (
        "---\n"
        f'target: "{item["target"]}"\n'
        f'target_blob: "{before}"\n'
        + design_meta +
        f'rubric_version: {data["rubric_version"]}\n'
        f'evaluator: "{CURRENT_EVALUATOR[0]}"\n'
        f'evaluator_model: "{CURRENT_EVALUATOR[1]}"\n'
        f'evaluated_at: "{timestamp}"\n'
        f'run_id: "{run_id}"\n'
        f'round: {args.round}\n'
        "---\n"
    )
    # Validate the persisted form in a sibling temp file before replacing the current evaluation.
    staged = destination.with_suffix(".md.staged")
    atomic_write(staged, frontmatter + raw.lstrip())
    try:
        persisted = staged.read_text(encoding="utf-8")
        if parse_metadata_text(persisted, args.slug, kind) is None or not validator(persisted, args.slug, kind_version(kind))["valid"]:
            raise SystemExit("persisted evaluation failed validation")
        if git_blob(target) != before:
            raise SystemExit("target changed before save")
        if kind == "article" and design_claim_changed(item):
            raise SystemExit("design changed before save")
        staged.replace(destination)
    finally:
        if staged.exists():
            staged.unlink()
    item["status"] = "success"
    item["evaluation"] = destination.as_posix()
    item["error"] = ""
    save_manifest(args.manifest, data)
    print(f"EVALUATION_SAVED slug={args.slug} file={destination} blob={before} round={args.round}")
    return 0


def _classify(path: Path, slug: str, kind: str, invalid: list[dict]) -> tuple[str, dict, dict] | None:
    """Return (status, meta, result) for an existing evaluation, or None when invalid/missing."""
    if not path.is_file():
        return None
    version = frontmatter_version(path)
    if version is None:
        invalid.append({"slug": slug, "file": path.as_posix(), "reason": "metadata"}); return None
    if version != kind_version(kind):
        return "legacy", {"rubric_version": str(version)}, {}
    meta = parse_metadata(path, slug, kind)
    if meta is None:
        invalid.append({"slug": slug, "file": path.as_posix(), "reason": "metadata"}); return None
    validator = validate_design_text if kind == "design" else validate_text
    result = validator(path.read_text(encoding="utf-8"), slug, kind_version(kind))
    if not result["valid"]:
        invalid.append({"slug": slug, "file": path.as_posix(), "reason": "output"}); return None
    return "", meta, result


def latest_design_evaluations(designs_dir: Path, evaluations_root: Path) -> tuple[list[dict], list[dict]]:
    if designs_dir.is_dir() and any(designs_dir.glob("*.md")):
        current_design_rubric_version(designs_dir)
    records: list[dict] = []; invalid: list[dict] = []
    for design in sorted(designs_dir.glob("*.md"), key=lambda p: p.stem):
        path = evaluation_path(evaluations_root, design.stem, "design")
        found = _classify(path, design.stem, "design", invalid)
        if found is None:
            records.append({"slug": design.stem, "status": "missing"}); continue
        status, meta, result = found
        if status != "legacy":
            status = "current" if meta["target_blob"] == git_blob(design) else "changed"
        records.append({"slug": design.stem, "status": status, "file": path.as_posix(),
                        "rubric_version": int(meta["rubric_version"]), "evaluation_blob": git_blob(path), **result})
    return records, invalid


def latest_evaluations(pages_dir: Path, evaluations_root: Path, rubric_version: int | None = None) -> tuple[list[dict], list[dict]]:
    current_version = rubric_version if rubric_version is not None else current_rubric_version(pages_dir)
    if current_version != CURRENT_RUBRIC_VERSION:
        raise ValueError(f"unsupported rubric_version: {current_version}")
    records: list[dict] = []
    invalid: list[dict] = []
    design_records, _ = latest_design_evaluations(pages_dir.parent / "designs", evaluations_root)
    designs_by_slug = {r["slug"]: r for r in design_records}
    for page in sorted(pages_dir.glob("*.md"), key=lambda p: p.stem):
        path = evaluation_path(evaluations_root, page.stem)
        found = _classify(path, page.stem, "article", invalid)
        if found is None:
            records.append({"slug": page.stem, "status": "missing", "design_state": "required"}); continue
        status, meta, result = found
        if status == "legacy":
            records.append({"slug": page.stem, "status": "legacy", "design_state": "required", "file": path.as_posix(),
                            "rubric_version": int(meta["rubric_version"])}); continue
        status = "current" if meta["target_blob"] == git_blob(page) else "changed"
        design = pages_dir.parent / "designs" / f"{page.stem}.md"
        latest_design = designs_by_slug.get(page.stem, {})
        dependency_current = bool(design.is_file() and git_blob(design) == meta["design_blob"] and
                                  latest_design.get("status") == "current" and
                                  latest_design.get("evaluation_blob") == meta["design_evaluation_blob"])
        design_state = "complete" if (status == "current" and dependency_current and result.get("pass") and
                                      result.get("design_alignment") == "合格" and latest_design.get("pass")) else "required"
        if status == "current" and not dependency_current:
            status = "design_required"
        records.append({"slug": page.stem, "status": status, "design_state": design_state,
                        "file": path.as_posix(), "rubric_version": int(meta["rubric_version"]), **result})
    return records, invalid


def cmd_evidence(args: argparse.Namespace) -> int:
    """Append one external verification to the slug's evidence log."""
    raw = args.body.read_text(encoding="utf-8").strip() + "\n"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        raise SystemExit(f"invalid slug: {args.slug}")
    headings = list(re.finditer(r"(?m)^## (.+?)[ \t]*$", raw))
    title = raw.splitlines()[0] if raw.strip() else ""
    if title != f"# 外部検証: {args.slug}" or tuple(h[1] for h in headings) != EVIDENCE_SECTIONS:
        print("外部検証本文は『# 外部検証: <slug>』と確認済み・未確認・誤りの三見出しを順に持つ必要があります", file=sys.stderr)
        return 1
    sections = {h[1]: raw[h.end():headings[i+1].start() if i+1 < len(headings) else len(raw)].strip()
                for i, h in enumerate(headings)}
    if not all(sections.values()):
        print("外部検証の各見出しは空にできません（該当なしは『- なし』）", file=sys.stderr)
        return 1
    target = Path(args.target)
    if target.as_posix() not in {target_path("article", args.slug), target_path("design", args.slug)} or not target.is_file():
        raise SystemExit("--target must be the slug's existing page or design")
    verified_at = args.verified_at or now()
    run_id = args.run_id or secrets.token_hex(6)
    if not re.fullmatch(r"[a-z0-9]{8,32}", run_id):
        raise SystemExit("run_id must be 8-32 lowercase alphanumerics")
    destination = args.evidence_root / f"{args.slug}.md"
    existing = destination.read_text(encoding="utf-8") if destination.is_file() else (
        f"# 外部検証記録: {args.slug}\n\n独立評価者による外部検証を検証ごとに追記する。過去の節は書き換えない。\n")
    if f"run={run_id}\n" in existing:
        raise SystemExit(f"evidence run already recorded: {run_id}")
    block = [f"\n## {verified_at} run={run_id}\n",
             f"- target: {target.as_posix()}", f"- target_blob: {git_blob(target)}",
             f"- evaluator: {CURRENT_EVALUATOR[0]} / {CURRENT_EVALUATOR[1]}", ""]
    for name in EVIDENCE_SECTIONS:
        block += [f"### {name}", "", sections[name], ""]
    atomic_write(destination, existing.rstrip("\n") + "\n" + "\n".join(block).rstrip("\n") + "\n")
    print(f"EVIDENCE_APPENDED slug={args.slug} file={destination} run_id={run_id}")
    return 0


def queue_rank(record: dict) -> tuple[int, str]:
    if record.get("reusability_gate") == "不合格": group = 0
    elif record.get("revision_count", 0): group = 1
    elif record.get("research_count", 0): group = 2
    else: group = 3
    return group, record["slug"]


def cmd_normalize(args: argparse.Namespace) -> int:
    records, invalid = latest_evaluations(args.pages_dir, args.evaluations_root, args.rubric_version)
    distribution = {"対象外": 0, "修正・調査必須": 0, "修正必須": 0, "調査必須": 0, "公開可": 0, "再評価必要": 0}
    for record in records:
        if record["status"] != "current": distribution["再評価必要"] += 1
        elif record.get("reusability_gate") == "不合格": distribution["対象外"] += 1
        elif record.get("revision_count") and record.get("research_count"): distribution["修正・調査必須"] += 1
        elif record.get("revision_count"): distribution["修正必須"] += 1
        elif record.get("research_count"): distribution["調査必須"] += 1
        else: distribution["公開可"] += 1
    current = [r for r in records if r["status"] == "current"]
    queue = sorted([r for r in current if not r.get("pass")], key=queue_rank)
    design_records, design_invalid = latest_design_evaluations(args.pages_dir.parent / "designs", args.evaluations_root)
    known_designs = {record["slug"] for record in design_records}
    missing_designs = [{"slug": page.stem, "status": "missing"}
                       for page in sorted(args.pages_dir.glob("*.md"), key=lambda path: path.stem)
                       if page.stem not in known_designs]
    output = {"design_records": design_records, "design_invalid_history": design_invalid,
              "design_improvement_queue": sorted([r for r in design_records if r["status"] == "current" and not r.get("pass")], key=queue_rank),
              "design_reevaluation_required": [r for r in design_records if r["status"] != "current"] + missing_designs,
              "process_distribution": {state: sum(r.get("design_state") == state for r in records)
                                       for state in ("complete", "required")},
              "records": records, "invalid_history": invalid, "distribution": distribution, "reevaluation_required": [r for r in records if r["status"] != "current"], "improvement_queue": queue}
    if args.output:
        atomic_write(args.output, json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--rubric-version", type=int, required=True)
    p.add_argument("--kind", choices=("article", "design"), default="article"); p.add_argument("--run-id"); p.add_argument("--target", action="append", default=[]); p.add_argument("--pages-dir"); p.add_argument("--designs-dir")
    p.add_argument("--evaluations-root", type=Path, default=EVALUATIONS_ROOT)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("next")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--limit", type=int, default=MAX_BATCH, choices=range(1, MAX_BATCH + 1)); p.set_defaults(func=cmd_next)
    p = sub.add_parser("fail")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--slug", required=True); p.add_argument("--error", required=True); p.set_defaults(func=cmd_fail)
    p = sub.add_parser("resume")
    p.add_argument("--manifest", type=Path, required=True); p.set_defaults(func=cmd_resume)
    p = sub.add_parser("save")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--slug", required=True); p.add_argument("--body", type=Path, required=True)
    p.add_argument("--round", type=int, required=True, help="1 for the initial evaluation, +1 for each re-evaluation in the same improvement loop")
    p.add_argument("--evaluations-root", type=Path, default=EVALUATIONS_ROOT); p.add_argument("--stage1", type=Path); p.add_argument("--evaluated-at"); p.add_argument("--evaluation-run-id"); p.set_defaults(func=cmd_save)
    p = sub.add_parser("evidence")
    p.add_argument("--slug", required=True); p.add_argument("--body", type=Path, required=True); p.add_argument("--target", required=True)
    p.add_argument("--evidence-root", type=Path, default=EVIDENCE_ROOT); p.add_argument("--verified-at"); p.add_argument("--run-id"); p.set_defaults(func=cmd_evidence)
    p = sub.add_parser("normalize")
    p.add_argument("--pages-dir", type=Path, default=Path("wiki/insight/pages")); p.add_argument("--evaluations-root", type=Path, default=EVALUATIONS_ROOT); p.add_argument("--rubric-version", type=int, choices=[CURRENT_RUBRIC_VERSION]); p.add_argument("--output", type=Path); p.set_defaults(func=cmd_normalize)
    return root


if __name__ == "__main__":
    cli = parser()
    arguments = cli.parse_args()
    raise SystemExit(arguments.func(arguments))
