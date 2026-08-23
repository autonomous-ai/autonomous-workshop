"""Inventor discovery and the deliberately small monorepo contract."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .errors import ManifestError

_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_AUTONOMY = frozenset(("autonomous", "human-checkpointed", "reference"))
_STATUS = frozenset(("active", "experimental", "blocked", "reference", "archived"))
_FIELDS = frozenset(
    (
        "schema_version", "id", "name", "niche", "summary", "autonomy",
        "status", "entrypoint", "capabilities", "core_features", "source",
    )
)
_SOURCE_KINDS = frozenset(("local", "upstream-snapshot"))
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _strings(value: Any, label: str, allow_empty: bool = False) -> Sequence[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ManifestError(
            "%s must be a %slist of strings"
            % (label, "possibly empty " if allow_empty else "non-empty ")
        )
    if len(value) > 100 or not all(
        isinstance(item, str)
        and item
        and len(item) <= 4096
        and not any(ord(character) < 32 or ord(character) == 127 for character in item)
        for item in value
    ):
        raise ManifestError(
            "%s must contain at most 100 bounded, control-free strings" % label
        )
    if len(value) != len(set(value)):
        raise ManifestError("%s must not contain duplicates" % label)
    return tuple(value)


@dataclass(frozen=True)
class InventorManifest:
    schema_version: int
    inventor_id: str
    name: str
    niche: str
    summary: str
    autonomy: str
    status: str
    entrypoint: Sequence[str]
    capabilities: Sequence[str]
    core_features: Sequence[str]
    source: Mapping[str, Any]
    path: Path

    @classmethod
    def parse(cls, raw: Mapping[str, Any], path: Path) -> "InventorManifest":
        unknown = set(raw) - _FIELDS
        if unknown:
            raise ManifestError("%s: unknown fields %s" % (path, sorted(unknown)))
        if raw.get("schema_version") != 1:
            raise ManifestError("%s: schema_version must be 1" % path)
        inventor_id = raw.get("id")
        if not isinstance(inventor_id, str) or not _ID.fullmatch(inventor_id):
            raise ManifestError("%s: id must match %s" % (path, _ID.pattern))
        if path.name == "inventor.json" and path.parent.name != inventor_id:
            raise ManifestError(
                "%s: id %r must match containing folder %r"
                % (path, inventor_id, path.parent.name)
            )
        values: Dict[str, str] = {}
        limits = {"name": 200, "niche": 500, "summary": 2_000}
        for key in ("name", "niche", "summary"):
            value = raw.get(key)
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > limits[key]
                or any(ord(character) < 32 or ord(character) == 127 for character in value)
            ):
                raise ManifestError(
                    "%s: %s must be one control-free string of at most %d characters"
                    % (path, key, limits[key])
                )
            values[key] = value.strip()
        autonomy = raw.get("autonomy")
        if autonomy not in _AUTONOMY:
            raise ManifestError("%s: autonomy must be one of %s" % (path, sorted(_AUTONOMY)))
        status = raw.get("status")
        if status not in _STATUS:
            raise ManifestError("%s: status must be one of %s" % (path, sorted(_STATUS)))
        if "core_features" not in raw:
            raise ManifestError("%s: core_features is required" % path)
        if "source" not in raw:
            raise ManifestError("%s: source is required" % path)
        source = raw.get("source")
        if not isinstance(source, Mapping) or source.get("kind") not in _SOURCE_KINDS:
            raise ManifestError(
                "%s: source kind must be one of %s" % (path, sorted(_SOURCE_KINDS))
            )
        if source["kind"] == "local":
            if set(source) != {"kind"}:
                raise ManifestError("%s: local source accepts only kind" % path)
        else:
            if set(source) != {"kind", "url", "commit", "imported_at"}:
                raise ManifestError(
                    "%s: upstream-snapshot source requires exactly url, commit, and imported_at"
                    % path
                )
            url = source.get("url")
            commit = source.get("commit")
            imported_at = source.get("imported_at")
            try:
                parsed_url = (
                    urllib.parse.urlsplit(url) if isinstance(url, str) else None
                )
            except ValueError:
                parsed_url = None
            if (
                parsed_url is None
                or len(url) > 2048
                or any(ord(character) < 32 or ord(character) == 127 for character in url)
                or parsed_url.scheme != "https"
                or not parsed_url.hostname
                or parsed_url.username is not None
                or parsed_url.password is not None
                or parsed_url.path in ("", "/")
                or parsed_url.query
                or parsed_url.fragment
            ):
                raise ManifestError(
                    "%s: upstream source url must be an absolute, credential-free "
                    "HTTPS repository URL without query or fragment" % path
                )
            if not isinstance(commit, str) or not _COMMIT.fullmatch(commit):
                raise ManifestError(
                    "%s: upstream source commit must be a full lowercase SHA" % path
                )
            try:
                if (
                    not isinstance(imported_at, str)
                    or date.fromisoformat(imported_at).isoformat() != imported_at
                ):
                    raise ValueError
            except ValueError:
                raise ManifestError(
                    "%s: upstream imported_at must be YYYY-MM-DD" % path
                )
        return cls(
            schema_version=1,
            inventor_id=inventor_id,
            name=values["name"],
            niche=values["niche"],
            summary=values["summary"],
            autonomy=autonomy,
            status=status,
            entrypoint=_strings(raw.get("entrypoint"), "entrypoint"),
            capabilities=_strings(raw.get("capabilities"), "capabilities"),
            core_features=_strings(raw.get("core_features", []), "core_features", True),
            source=dict(source),
            path=path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.inventor_id,
            "name": self.name,
            "niche": self.niche,
            "summary": self.summary,
            "autonomy": self.autonomy,
            "status": self.status,
            "entrypoint": list(self.entrypoint),
            "capabilities": list(self.capabilities),
            "core_features": list(self.core_features),
            "source": dict(self.source),
        }


def load_manifest(path: Path) -> InventorManifest:
    path = Path(path)
    if path.is_symlink():
        raise ManifestError("inventor manifest must not be a symlink: %s" % path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError("missing inventor manifest: %s" % path)
    except (OSError, ValueError) as exc:
        raise ManifestError("cannot read %s: %s" % (path, exc))
    if not isinstance(raw, Mapping):
        raise ManifestError("%s: top level must be an object" % path)
    return InventorManifest.parse(raw, path)


def inventor_collection(root: Path) -> Path:
    """Resolve a repository root or an inventor-collection root safely."""

    root = Path(root).resolve(strict=True)
    nested = root / "inventors"
    if nested.is_symlink():
        raise ManifestError("inventors collection must not be a symlink: %s" % nested)
    if nested.exists():
        if not nested.is_dir():
            raise ManifestError("inventors collection must be a directory: %s" % nested)
        return nested.resolve(strict=True)
    return root


def discover_inventors(root: Path) -> List[InventorManifest]:
    collection = inventor_collection(root)
    manifests = []
    seen = set()
    for path in sorted(collection.glob("*/inventor.json")):
        if path.parent.is_symlink():
            raise ManifestError(
                "inventor folder must not be a symlink: %s" % path.parent
            )
        taste_path = path.parent / "TASTE.md"
        if taste_path.is_symlink() or not taste_path.is_file():
            raise ManifestError(
                "inventor folder must contain a regular TASTE.md: %s" % path.parent
            )
        try:
            taste_bytes = taste_path.read_bytes()
            taste_text = taste_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ManifestError("cannot read %s: %s" % (taste_path, exc))
        if not taste_text.strip() or len(taste_bytes) > 262144:
            raise ManifestError(
                "inventor TASTE.md must be non-empty UTF-8 at most 262144 bytes: %s"
                % taste_path
            )
        manifest = load_manifest(path)
        if manifest.inventor_id in seen:
            raise ManifestError("duplicate inventor id %r" % manifest.inventor_id)
        seen.add(manifest.inventor_id)
        manifests.append(manifest)
    if not manifests:
        raise ManifestError("inventor collection has no manifests: %s" % collection)
    return manifests


def validate_entrypoints(manifests: Iterable[InventorManifest]) -> List[str]:
    """Return actionable filesystem errors without executing inventor code."""
    def is_contained_file(base: Path, candidate: Path) -> bool:
        try:
            resolved_base = base.resolve(strict=True)
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(resolved_base)
        except (OSError, ValueError):
            return False
        return resolved.is_file()

    problems = []
    for manifest in manifests:
        command = manifest.entrypoint
        if not command or command[0] not in ("python", "python3", "bash", "sh"):
            problems.append(
                "%s: entrypoint runner must be python/python3/bash/sh"
                % manifest.inventor_id
            )
            continue
        if len(command) < 2:
            problems.append("%s: entrypoint must name a local module or script" % manifest.inventor_id)
            continue
        if command[1] == "-m" and len(command) >= 3:
            if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", command[2]):
                problems.append(
                    "%s: entrypoint module %r is invalid"
                    % (manifest.inventor_id, command[2])
                )
                continue
            module = Path(*command[2].split("."))
            base = manifest.path.parent
            candidates = (
                base / module.with_suffix(".py"),
                base / module / "__main__.py",
                base / "src" / module.with_suffix(".py"),
                base / "src" / module / "__main__.py",
            )
            if not any(is_contained_file(base, candidate) for candidate in candidates):
                problems.append(
                    "%s: entrypoint module %s is missing"
                    % (manifest.inventor_id, command[2])
                )
            continue
        if command[1].startswith("-"):
            problems.append(
                "%s: unsupported interpreter flag %r in entrypoint"
                % (manifest.inventor_id, command[1])
            )
            continue
        relative = Path(command[1])
        if relative.is_absolute() or ".." in relative.parts or "\\" in command[1]:
            problems.append(
                "%s: entrypoint script must stay inside its inventor folder"
                % manifest.inventor_id
            )
            continue
        candidate = manifest.path.parent / relative
        if command[0] in ("python", "python3", "bash", "sh") and not is_contained_file(
            manifest.path.parent, candidate
        ):
            problems.append(
                "%s: entrypoint target %s is missing"
                % (manifest.inventor_id, relative.as_posix())
            )
    return problems
