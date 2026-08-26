"""Strict schema-v8 Inventor discovery and manifest validation."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, List, Mapping, Sequence

from workshop.contributors.extensions import (
    InventorExtension,
    parse_inventor_extensions,
)
from workshop.errors import ManifestError


_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_STATUS = frozenset(("active", "experimental", "blocked", "reference", "archived"))
_FIELDS = frozenset(("schema_version", "id", "status", "source", "extensions"))
_SOURCE_KINDS = frozenset(("local", "upstream-snapshot"))
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _source(value: Any, path: Path) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("kind") not in _SOURCE_KINDS:
        raise ManifestError(
            "%s: source kind must be one of %s" % (path, sorted(_SOURCE_KINDS))
        )
    if value["kind"] == "local":
        if set(value) != {"kind"}:
            raise ManifestError("%s: local source accepts only kind" % path)
        return {"kind": "local"}

    if set(value) != {"kind", "url", "commit", "imported_at"}:
        raise ManifestError(
            "%s: upstream-snapshot source requires exactly url, commit, and imported_at"
            % path
        )
    url = value.get("url")
    commit = value.get("commit")
    imported_at = value.get("imported_at")
    try:
        parsed_url = urllib.parse.urlsplit(url) if isinstance(url, str) else None
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
            "%s: upstream source url must be an absolute, credential-free HTTPS "
            "repository URL without query or fragment" % path
        )
    if not isinstance(commit, str) or _COMMIT.fullmatch(commit) is None:
        raise ManifestError(
            "%s: upstream source commit must be a full lowercase SHA" % path
        )
    try:
        if (
            not isinstance(imported_at, str)
            or date.fromisoformat(imported_at).isoformat() != imported_at
        ):
            raise ValueError
    except ValueError as exc:
        raise ManifestError(
            "%s: upstream imported_at must be YYYY-MM-DD" % path
        ) from exc
    return dict(value)


@dataclass(frozen=True)
class InventorManifest:
    """One exact native Inventor bundle; no executable profile contract."""

    schema_version: int
    inventor_id: str
    status: str
    source: Mapping[str, Any]
    extensions: Sequence[InventorExtension]
    path: Path

    @classmethod
    def parse(cls, raw: Mapping[str, Any], path: Path) -> "InventorManifest":
        if type(raw.get("schema_version")) is not int or raw["schema_version"] != 8:
            raise ManifestError("%s: schema_version must be 8" % path)
        if set(raw) != _FIELDS:
            missing = sorted(_FIELDS - set(raw))
            unknown = sorted(set(raw) - _FIELDS)
            details = []
            if missing:
                details.append("missing fields %s" % missing)
            if unknown:
                details.append("unknown fields %s" % unknown)
            raise ManifestError("%s: %s" % (path, "; ".join(details)))
        inventor_id = raw.get("id")
        if not isinstance(inventor_id, str) or _ID.fullmatch(inventor_id) is None:
            raise ManifestError("%s: id must match %s" % (path, _ID.pattern))
        if path.name == "inventor.json" and path.parent.name != inventor_id:
            raise ManifestError(
                "%s: id %r must match containing folder %r"
                % (path, inventor_id, path.parent.name)
            )
        status = raw.get("status")
        if status not in _STATUS:
            raise ManifestError("%s: status must be one of %s" % (path, sorted(_STATUS)))
        source = _source(raw.get("source"), path)
        extensions = parse_inventor_extensions(
            raw.get("extensions"), inventor_id=inventor_id
        )
        return cls(
            schema_version=8,
            inventor_id=inventor_id,
            status=status,
            source=source,
            extensions=extensions,
            path=Path(path),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 8,
            "id": self.inventor_id,
            "status": self.status,
            "source": dict(self.source),
            "extensions": [item.to_dict() for item in self.extensions],
        }


def load_manifest(path: Path) -> InventorManifest:
    path = Path(path)
    if path.is_symlink():
        raise ManifestError("inventor manifest must not be a symlink: %s" % path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError("missing inventor manifest: %s" % path) from exc
    except (OSError, ValueError) as exc:
        raise ManifestError("cannot read %s: %s" % (path, exc)) from exc
    if not isinstance(raw, Mapping):
        raise ManifestError("%s: top level must be an object" % path)
    return InventorManifest.parse(raw, path)


def inventor_collection(root: Path) -> Path:
    """Resolve a repository root or an inventor-collection root safely."""

    requested = Path(root)
    if requested.is_symlink():
        raise ManifestError("inventor collection must not be a symlink: %s" % requested)
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("cannot resolve inventor collection: %s" % requested) from exc
    if not resolved.is_dir():
        raise ManifestError("inventor collection must be a directory: %s" % resolved)
    nested = resolved / "inventors"
    if nested.is_symlink():
        raise ManifestError("inventors collection must not be a symlink: %s" % nested)
    if nested.exists():
        if not nested.is_dir():
            raise ManifestError("inventors collection must be a directory: %s" % nested)
        return nested.resolve(strict=True)
    return resolved


def discover_inventors(root: Path) -> List[InventorManifest]:
    collection = inventor_collection(root)
    manifests: list[InventorManifest] = []
    seen: set[str] = set()
    for path in sorted(collection.glob("*/inventor.json")):
        if path.parent.is_symlink():
            raise ManifestError("inventor folder must not be a symlink: %s" % path.parent)
        taste_path = path.parent / "TASTE.md"
        if taste_path.is_symlink() or not taste_path.is_file():
            raise ManifestError(
                "inventor folder must contain a regular TASTE.md: %s" % path.parent
            )
        manifest = load_manifest(path)
        if manifest.inventor_id in seen:
            raise ManifestError("duplicate inventor id %r" % manifest.inventor_id)
        seen.add(manifest.inventor_id)
        manifests.append(manifest)
    if not manifests:
        raise ManifestError("inventor collection has no manifests: %s" % collection)
    return manifests


__all__ = [
    "InventorManifest",
    "discover_inventors",
    "inventor_collection",
    "load_manifest",
]
