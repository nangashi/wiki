"""Configuration loader for collection-independent wiki tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.8--3.10
    from _vendor import tomli as tomllib


COLLECTION_ID = re.compile(r"[a-z0-9][a-z0-9-]*")


class ConfigError(ValueError):
    """Raised when the wiki registry or a collection configuration is invalid."""


@dataclass(frozen=True)
class Publication:
    mode: str
    command: tuple[str, ...] | None


@dataclass(frozen=True)
class Collection:
    id: str
    purpose: str
    directory: Path
    pages: Path
    index: Path
    schema: Path
    workflows: dict[str, Path]
    checks: tuple[tuple[str, ...], ...]
    publication: Publication


def _read_toml(path: Path) -> dict:
    try:
        with path.open("rb") as source:
            data = tomllib.load(source)
    except OSError as error:
        raise ConfigError(f"設定を読めません: {path}: {error}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"設定が不正です: {path}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"設定が不正です: {path}")
    return data


def _relative(base: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ConfigError(f"{label} は相対パスで指定してください")
    return base / value


def _required_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise ConfigError(f"{label} がありません: {path}")
    return path


def _required_directory(path: Path, label: str) -> Path:
    if not path.is_dir():
        raise ConfigError(f"{label} がありません: {path}")
    return path


def load(root: Path) -> dict[str, Collection]:
    """Load registered collections, resolving all configured paths from *root*."""
    root = root.resolve()
    registry = _read_toml(root / "wiki" / "collections.toml")
    entries = registry.get("collections")
    if not isinstance(entries, dict) or not entries:
        raise ConfigError("wiki/collections.toml に [collections] がありません")
    collections: dict[str, Collection] = {}
    for collection_id, config_name in entries.items():
        if not isinstance(collection_id, str) or not COLLECTION_ID.fullmatch(collection_id):
            raise ConfigError("collection ID が不正です")
        config_path = _relative(root / "wiki", config_name, f"collections.{collection_id}")
        raw = _read_toml(config_path)
        if raw.get("id") != collection_id:
            raise ConfigError(f"{config_path} の id は {collection_id!r} である必要があります")
        purpose = raw.get("purpose")
        if not isinstance(purpose, str) or not purpose:
            raise ConfigError(f"{config_path} の purpose がありません")
        base = config_path.parent
        workflows_raw = raw.get("workflows", {})
        if not isinstance(workflows_raw, dict):
            raise ConfigError(f"{config_path} の [workflows] が不正です")
        if set(("ingest", "review", "lint")) - set(workflows_raw):
            raise ConfigError(f"{config_path} の [workflows] には ingest, review, lint が必要です")
        workflows = {name: _required_file(_relative(base, value, f"{config_path} workflows.{name}"),
                                          f"{config_path} workflows.{name}")
                     for name, value in workflows_raw.items() if isinstance(name, str)}
        checks_table = raw.get("checks", {})
        if not isinstance(checks_table, dict):
            raise ConfigError(f"{config_path} の [checks] が不正です")
        checks_raw = checks_table.get("commands", [])
        if not isinstance(checks_raw, list) or any(not isinstance(command, list) or not command or
                                                   any(not isinstance(arg, str) for arg in command)
                                                   for command in checks_raw):
            raise ConfigError(f"{config_path} の checks.commands が不正です")
        publication_raw = raw.get("publication", {})
        if not isinstance(publication_raw, dict):
            raise ConfigError(f"{config_path} の [publication] が不正です")
        mode = publication_raw.get("mode")
        command = publication_raw.get("command")
        if mode not in ("direct", "checked"):
            raise ConfigError(f"{config_path} の publication.mode が不正です")
        if command is not None and (not isinstance(command, list) or not command or any(not isinstance(arg, str) for arg in command)):
            raise ConfigError(f"{config_path} の publication.command が不正です")
        if mode == "checked" and command is None:
            raise ConfigError(f"{config_path} の checked publication には command が必要です")
        collections[collection_id] = Collection(
            id=collection_id, purpose=purpose, directory=base,
            pages=_required_directory(_relative(base, raw.get("pages"), f"{config_path} pages"), f"{config_path} pages"),
            index=_required_file(_relative(base, raw.get("index"), f"{config_path} index"), f"{config_path} index"),
            schema=_required_file(_relative(base, raw.get("schema"), f"{config_path} schema"), f"{config_path} schema"),
            workflows=workflows, checks=tuple(tuple(item) for item in checks_raw),
            publication=Publication(mode, tuple(command) if command else None),
        )
    return collections
