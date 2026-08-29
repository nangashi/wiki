#!/usr/bin/env python3
"""State and persistence helper for bulk insight evaluations.

The helper never launches Codex.  Claude Code owns process creation; this
module only prepares/claims work, validates results, adds trusted metadata,
saves history, resumes interrupted runs, and rebuilds the quality queue.
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

from evaluation_validator import validate_text
from insight_source_validator import validate as validate_sources

MAX_BATCH = 3
MAX_ATTEMPTS = 3  # initial attempt plus two clean retries


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


def parse_metadata(path: Path, expected_slug: str) -> dict | None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    if len(match.group(1).splitlines()) != 7:
        return None
    pairs = re.findall(r'(?m)^([a-z_]+): (?:(?:"([^"]*)")|([0-9]+))$', match.group(1))
    meta = {key: quoted if quoted != "" else bare for key, quoted, bare in pairs}
    required = {"target", "target_blob", "rubric_version", "evaluator", "evaluator_model", "evaluated_at", "run_id"}
    if set(meta) != required:
        return None
    filename = re.fullmatch(r"([0-9]{8}T[0-9]{6}Z)-v([0-9]+)-([a-z0-9]{8,32})\.md", path.name)
    if not filename:
        return None
    stamp = meta["evaluated_at"].replace("-", "").replace(":", "")
    if filename.groups() != (stamp, meta["rubric_version"], meta["run_id"]):
        return None
    if meta["target"] != f"wiki/insight/pages/{expected_slug}.md":
        return None
    if meta["evaluator"] != "codex" or meta["evaluator_model"] != "gpt-5.6-sol":
        return None
    if not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", meta["target_blob"]):
        return None
    try:
        dt.datetime.strptime(meta["evaluated_at"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return meta


def cmd_init(args: argparse.Namespace) -> int:
    targets: list[tuple[str, str]] = []
    for spec in args.target:
        slug, sep, path = spec.partition(":")
        if not sep or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise SystemExit(f"invalid --target: {spec}")
        targets.append((slug, path))
    if args.pages_dir:
        targets.extend((p.stem, f"wiki/insight/pages/{p.name}") for p in Path(args.pages_dir).glob("*.md"))
    unique = dict(sorted(set(targets)))
    if not unique:
        raise SystemExit("at least one --target or --pages-dir is required")
    data = {
        "schema_version": 1, "run_id": args.run_id or secrets.token_hex(6),
        "rubric_version": args.rubric_version, "started_at": now(), "updated_at": now(),
        "items": [{"slug": slug, "target": target, "status": "pending", "attempts": 0,
                   "evaluation": "", "error": ""} for slug, target in unique.items()],
    }
    save_manifest(args.manifest, data)
    print(f"RUN_INITIALIZED run_id={data['run_id']} total={len(data['items'])} manifest={args.manifest}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    candidates = [i for i in data["items"] if i["status"] in {"pending", "retry"}]
    selected = candidates[: min(args.limit, MAX_BATCH)]
    for item in selected:
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
    count = 0
    for item in data["items"]:
        if item["status"] == "running":
            item["status"] = "retry" if item["attempts"] < MAX_ATTEMPTS else "failed"
            item["error"] = item.get("error") or "interrupted"
            count += 1
    save_manifest(args.manifest, data)
    print(f"RUN_RESUMED reset_running={count}")
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    data = load(args.manifest)
    item = item_for(data, args.slug)
    if item["status"] != "running":
        raise SystemExit(f"{args.slug} is not running")
    raw = args.body.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        print("Codex本文にfrontmatterを含めることはできません", file=sys.stderr)
        return 1
    result = validate_text(raw, args.slug)
    if not result["valid"]:
        print("; ".join(result["errors"]), file=sys.stderr)
        return 1
    target = Path(item["target"])
    source_diagnostics = validate_sources(target)
    structural = [item for item in source_diagnostics if item.category == "structure"]
    quality = [item for item in source_diagnostics if item.category == "quality"]
    if structural:
        for item in structural:
            print(f"{item.code}: {item.reason}", file=sys.stderr)
        print("target article has structurally invalid external sources", file=sys.stderr)
        return 1
    if quality:
        blocking_text = "\n".join(result.get("blocking_issues", []))
        source_blocking = all(item.code in blocking_text for item in quality)
        if result.get("score_cap") != 49 or result.get("pass") or not source_blocking:
            for item in quality:
                print(f"{item.code}: {item.reason}", file=sys.stderr)
            print("source quality issue requires a matching Blocking, score_cap=49 and pass=いいえ", file=sys.stderr)
            return 1
    before = git_blob(target)
    timestamp = args.evaluated_at or now()
    run_id = args.evaluation_run_id or secrets.token_hex(6)
    if not re.fullmatch(r"[a-z0-9]{8,32}", run_id):
        raise SystemExit("evaluation run_id must be 8-32 lowercase alphanumerics")
    filename_stamp = timestamp.replace("-", "").replace(":", "")
    destination = args.evaluations_root / args.slug / f"{filename_stamp}-v{data['rubric_version']}-{run_id}.md"
    if destination.exists():
        raise SystemExit(f"evaluation already exists: {destination}")
    frontmatter = (
        "---\n"
        f'target: "{item["target"]}"\n'
        f'target_blob: "{before}"\n'
        f'rubric_version: {data["rubric_version"]}\n'
        'evaluator: "codex"\n'
        'evaluator_model: "gpt-5.6-sol"\n'
        f'evaluated_at: "{timestamp}"\n'
        f'run_id: "{run_id}"\n'
        "---\n"
    )
    if git_blob(target) != before:
        raise SystemExit("target changed before save")
    atomic_write(destination, frontmatter + raw.lstrip())
    # Validate what was persisted, including trusted metadata.
    if parse_metadata(destination, args.slug) is None or not validate_text(destination.read_text(encoding="utf-8"), args.slug)["valid"]:
        destination.unlink()
        raise SystemExit("persisted evaluation failed validation")
    if git_blob(target) != before:
        destination.unlink()
        raise SystemExit("target changed during save")
    item["status"] = "success"
    item["evaluation"] = destination.as_posix()
    item["error"] = ""
    save_manifest(args.manifest, data)
    print(f"EVALUATION_SAVED slug={args.slug} file={destination} blob={before}")
    return 0


def latest_evaluations(pages_dir: Path, evaluations_root: Path) -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    invalid: list[dict] = []
    for page in sorted(pages_dir.glob("*.md"), key=lambda p: p.stem):
        valid: list[tuple[str, str, Path, dict, dict]] = []
        directory = evaluations_root / page.stem
        if directory.is_dir():
            for candidate in sorted(directory.glob("*.md")):
                meta = parse_metadata(candidate, page.stem)
                result = validate_text(candidate.read_text(encoding="utf-8"), page.stem)
                if meta is None or not result["valid"]:
                    invalid.append({"slug": page.stem, "file": candidate.as_posix(),
                                    "reason": "metadata" if meta is None else "output"})
                    continue
                valid.append((meta["evaluated_at"], meta["run_id"], candidate, meta, result))
        if not valid:
            records.append({"slug": page.stem, "status": "missing"})
            continue
        _, _, candidate, meta, result = max(valid, key=lambda value: (value[0], value[1]))
        records.append({"slug": page.stem, "status": "current" if meta["target_blob"] == git_blob(page) else "changed",
                        "file": candidate.as_posix(), "rubric_version": int(meta["rubric_version"]), **result})
    return records, invalid


def queue_rank(record: dict) -> tuple[int, int, str]:
    score = record.get("final_score")
    normalized = score if isinstance(score, int) else -1
    if record.get("reusability_gate") == "不合格" or record.get("blocking_count", 0):
        group = 0
    elif record.get("major_count", 0):
        group = 1
    elif normalized < 60:
        group = 2
    elif normalized < 70:
        group = 3
    else:
        group = 4
    return group, normalized, record["slug"]


def cmd_normalize(args: argparse.Namespace) -> int:
    records, invalid = latest_evaluations(args.pages_dir, args.evaluations_root)
    distribution = {"採点対象外": 0, "0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0, "missing_or_changed": 0}
    for record in records:
        if record["status"] != "current":
            distribution["missing_or_changed"] += 1
        elif record.get("final_score") is None:
            distribution["採点対象外"] += 1
        else:
            score = record["final_score"]
            band = "0-59" if score < 60 else "60-69" if score < 70 else "70-79" if score < 80 else "80-89" if score < 90 else "90-100"
            distribution[band] += 1
    current = [r for r in records if r["status"] == "current"]
    queue = sorted([r for r in current if r.get("blocking_count", 0) or r.get("major_count", 0) or r.get("final_score") is None or r.get("final_score", 100) < 70], key=queue_rank)
    output = {"records": records, "invalid_history": invalid, "distribution": distribution, "improvement_queue": queue}
    if args.output:
        atomic_write(args.output, json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--rubric-version", type=int, required=True)
    p.add_argument("--run-id"); p.add_argument("--target", action="append", default=[]); p.add_argument("--pages-dir")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("next")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--limit", type=int, default=MAX_BATCH, choices=range(1, MAX_BATCH + 1)); p.set_defaults(func=cmd_next)
    p = sub.add_parser("fail")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--slug", required=True); p.add_argument("--error", required=True); p.set_defaults(func=cmd_fail)
    p = sub.add_parser("resume")
    p.add_argument("--manifest", type=Path, required=True); p.set_defaults(func=cmd_resume)
    p = sub.add_parser("save")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--slug", required=True); p.add_argument("--body", type=Path, required=True)
    p.add_argument("--evaluations-root", type=Path, default=Path("evaluations/insight")); p.add_argument("--evaluated-at"); p.add_argument("--evaluation-run-id"); p.set_defaults(func=cmd_save)
    p = sub.add_parser("normalize")
    p.add_argument("--pages-dir", type=Path, default=Path("wiki/insight/pages")); p.add_argument("--evaluations-root", type=Path, default=Path("evaluations/insight")); p.add_argument("--output", type=Path); p.set_defaults(func=cmd_normalize)
    return root


if __name__ == "__main__":
    cli = parser()
    arguments = cli.parse_args()
    raise SystemExit(arguments.func(arguments))
