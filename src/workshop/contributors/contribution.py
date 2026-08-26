"""Entirely static checks for schema-v8 Inventor contributions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from workshop.contributors.extensions import load_inventor_extension_bundles
from workshop.contributors.manifest import (
    InventorManifest,
    discover_inventors,
    load_manifest,
)
from workshop.contributors.taste import load_taste_header
from workshop.errors import ManifestError


ROUTABLE_INVENTOR_STATUSES = frozenset(("active", "experimental"))


def _regular_file(path: Path) -> bool:
    return not path.is_symlink() and path.is_file()


def validate_contribution(manifest: InventorManifest) -> List[str]:
    """Return actionable problems without importing or executing extension code."""

    root = manifest.path.parent
    problems: list[str] = []
    taste = root / "TASTE.md"
    if not _regular_file(taste):
        problems.append(
            "%s: Inventor requires a regular TASTE.md" % manifest.inventor_id
        )
    else:
        try:
            load_taste_header(root)
        except ManifestError as exc:
            problems.append(
                "%s: invalid TASTE.md discovery header: %s"
                % (manifest.inventor_id, exc)
            )

    try:
        children = tuple(root.iterdir())
    except OSError as exc:
        problems.append(
            "%s: cannot inspect Inventor folder: %s"
            % (manifest.inventor_id, exc)
        )
        return problems
    allowed = {"inventor.json", "TASTE.md", "README.md", "skills"}
    extras = sorted(child.name for child in children if child.name not in allowed)
    if extras:
        problems.append(
            "%s: Inventor folder may contain only inventor.json, TASTE.md, skills, "
            "and optional README.md; remove %s" % (manifest.inventor_id, extras)
        )

    try:
        load_inventor_extension_bundles(manifest)
    except ManifestError as exc:
        problems.append(
            "%s: invalid Inventor extension bundle: %s"
            % (manifest.inventor_id, exc)
        )

    readme = root / "README.md"
    if readme.exists() or readme.is_symlink():
        if not _regular_file(readme):
            problems.append(
                "%s: optional README.md must be a regular file" % manifest.inventor_id
            )
        else:
            try:
                readme_size = readme.stat().st_size
            except OSError:
                readme_size = -1
            if not 1 <= readme_size <= 32 * 1024:
                problems.append(
                    "%s: optional README.md must contain 1 to 32768 bytes"
                    % manifest.inventor_id
                )
    return problems


def manifests_for_target(target: Path) -> Sequence[InventorManifest]:
    """Resolve an Inventor folder, manifest, repository, or collection."""

    target = Path(os.path.abspath(os.fspath(target)))
    if target.is_symlink():
        raise ManifestError("contribution target must not be a symlink: %s" % target)
    if target.name == "inventor.json":
        return (load_manifest(target),)
    if (target / "inventor.json").is_file():
        return (load_manifest(target / "inventor.json"),)
    return tuple(discover_inventors(target))


def check_target(target: Path) -> List[str]:
    """Statically validate every Inventor resolved from ``target``."""

    return [
        problem
        for manifest in manifests_for_target(target)
        for problem in validate_contribution(manifest)
    ]


def validate_inventor_collection(
    root: Path, *, required_routable_id: Optional[str] = None
) -> Tuple[InventorManifest, ...]:
    """Validate a complete contributor-owned Inventor collection."""

    requested = Path(root)
    if requested.is_symlink():
        raise ManifestError(
            "inventor collection root must not be a symlink: %s" % requested
        )
    try:
        collection = requested.resolve(strict=True)
    except OSError as exc:
        raise ManifestError(
            "cannot resolve inventor collection %s: %s" % (requested, exc)
        ) from exc
    if not collection.is_dir():
        raise ManifestError("inventor collection must be a directory: %s" % collection)

    try:
        entries = tuple(sorted(collection.iterdir(), key=lambda item: item.name))
    except OSError as exc:
        raise ManifestError(
            "cannot list inventor collection %s: %s" % (collection, exc)
        ) from exc
    for entry in entries:
        if entry.is_symlink():
            raise ManifestError(
                "inventor collection must not contain symlinks: %s" % entry
            )
        if not entry.is_dir():
            continue
        manifest_path = entry / "inventor.json"
        taste_path = entry / "TASTE.md"
        has_manifest = manifest_path.exists() or manifest_path.is_symlink()
        has_taste = taste_path.exists() or taste_path.is_symlink()
        if has_manifest != has_taste:
            missing = taste_path if has_manifest else manifest_path
            raise ManifestError("inventor folder is missing %s" % missing)

    manifests = tuple(discover_inventors(collection))
    problems = [
        problem
        for manifest in manifests
        for problem in validate_contribution(manifest)
    ]
    if problems:
        raise ManifestError("; ".join(problems))
    if required_routable_id is not None:
        selected = next(
            (
                manifest
                for manifest in manifests
                if manifest.inventor_id == required_routable_id
            ),
            None,
        )
        if selected is None:
            raise ManifestError(
                "inventor collection is missing %s" % required_routable_id
            )
        if selected.status not in ROUTABLE_INVENTOR_STATUSES:
            raise ManifestError("created inventor is not routable")
    return manifests


__all__ = [
    "check_target",
    "manifests_for_target",
    "validate_contribution",
    "validate_inventor_collection",
]
