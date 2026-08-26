"""Static checks for native inventor-persona contributions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from workshop.errors import ManifestError
from workshop.contributors.manifest import (
    InventorManifest,
    discover_inventors,
    load_manifest,
    validate_entrypoints,
)
from workshop.contributors.taste import load_taste_header
from workshop.contributors.contracts import ROUTABLE_INVENTOR_STATUSES


def _regular_file(path: Path) -> bool:
    return not path.is_symlink() and path.is_file()


def validate_contribution(manifest: InventorManifest) -> List[str]:
    """Return actionable, entirely static problems for one persona folder."""

    problems = list(validate_entrypoints((manifest,)))
    root = manifest.path.parent
    if manifest.source.get("kind") == "local" and manifest.schema_version != 6:
        problems.append(
            "%s: local inventors must use native persona schema_version 6"
            % manifest.inventor_id
        )
        return problems
    if not manifest.native_persona:
        return problems
    if not _regular_file(root / "TASTE.md"):
        problems.append(
            "%s: local inventor requires a regular TASTE.md"
            % manifest.inventor_id
        )
    if _regular_file(root / "TASTE.md"):
        try:
            load_taste_header(root)
        except ManifestError as exc:
            problems.append("%s: invalid TASTE.md discovery header: %s" % (
                manifest.inventor_id,
                exc,
            ))
    allowed = {"inventor.json", "TASTE.md", "README.md"}
    try:
        children = tuple(root.iterdir())
    except OSError as exc:
        problems.append(
            "%s: cannot inspect native persona folder: %s"
            % (manifest.inventor_id, exc)
        )
        return problems
    extras = sorted(child.name for child in children if child.name not in allowed)
    if extras:
        problems.append(
            "%s: native persona folder may contain only inventor.json, TASTE.md, "
            "and optional README.md; remove %s"
            % (manifest.inventor_id, extras)
        )
    readme = root / "README.md"
    if readme.exists() or readme.is_symlink():
        if not _regular_file(readme):
            problems.append(
                "%s: optional README.md must be a regular file"
                % manifest.inventor_id
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


def run_declared_checks(manifest: InventorManifest) -> List[str]:
    """Compatibility alias for static validation; native personas run no code."""

    return validate_contribution(manifest)


def manifests_for_target(target: Path) -> Sequence[InventorManifest]:
    """Resolve an inventor folder, manifest, repository, or collection."""

    # Keep paths absolute before loading manifests.
    # A relative ``.`` otherwise leaves the manifest parent named ``.`` and
    # breaks the invariant that an inventor id matches its folder name.
    target = Path(os.path.abspath(os.fspath(target)))
    if target.is_symlink():
        raise ManifestError("contribution target must not be a symlink: %s" % target)
    if target.name == "inventor.json":
        return (load_manifest(target),)
    if (target / "inventor.json").is_file():
        return (load_manifest(target / "inventor.json"),)
    return tuple(discover_inventors(target))


def check_target(target: Path, *, run: bool = False) -> List[str]:
    problems: List[str] = []
    for manifest in manifests_for_target(target):
        observed = (
            run_declared_checks(manifest)
            if run
            else validate_contribution(manifest)
        )
        problems.extend(observed)
    return problems


def validate_inventor_collection(
    root: Path, *, required_routable_id: Optional[str] = None
) -> Tuple[InventorManifest, ...]:
    """Validate contributor-owned catalog structure without importing Match.

    Match owns semantic selection. Contributors owns whether a collection
    contains complete native personas, which is the only fact atomic
    scaffolding needs before publication.
    """

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
    contribution_problems = [
        problem
        for manifest in manifests
        for problem in validate_contribution(manifest)
    ]
    if contribution_problems:
        raise ManifestError("; ".join(contribution_problems))
    for manifest in manifests:
        load_taste_header(manifest.path.parent)
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
    "run_declared_checks",
    "validate_inventor_collection",
    "validate_contribution",
]
