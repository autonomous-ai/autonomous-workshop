"""Static and executable checks for inventor pull requests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from workshop.errors import ManifestError
from workshop.contributors.manifest import InventorManifest, discover_inventors, load_manifest, validate_entrypoints
from workshop.contributors.taste import load_taste_header
from workshop.contributors.contracts import ROUTABLE_INVENTOR_STATUSES


def _regular_file(path: Path) -> bool:
    return not path.is_symlink() and path.is_file()


def validate_contribution(manifest: InventorManifest) -> List[str]:
    """Return actionable repository-contract problems for one inventor.

    This check intentionally does not import or execute inventor code. Use
    :func:`run_declared_checks` only when executing code from the contribution
    is appropriate (for example, locally or in an isolated CI job).
    """

    problems = list(validate_entrypoints((manifest,)))
    root = manifest.path.parent
    if manifest.source.get("kind") != "local":
        return problems
    if manifest.schema_version != 5:
        problems.append(
            "%s: local inventors must use operational manifest schema_version 5"
            % manifest.inventor_id
        )
    for filename in ("README.md", "TASTE.md"):
        if not _regular_file(root / filename):
            problems.append(
                "%s: local inventor requires a regular %s"
                % (manifest.inventor_id, filename)
            )
    if _regular_file(root / "TASTE.md"):
        try:
            load_taste_header(root)
        except ManifestError as exc:
            problems.append("%s: invalid TASTE.md discovery header: %s" % (
                manifest.inventor_id,
                exc,
            ))
    tests = root / "tests"
    if tests.is_symlink() or not tests.is_dir():
        problems.append(
            "%s: local inventor requires a tests/ directory"
            % manifest.inventor_id
        )
    else:
        test_files = [
            path
            for path in tests.glob("test_*.py")
            if _regular_file(path)
        ]
        if not test_files:
            problems.append(
                "%s: tests/ must contain a regular test_*.py file"
                % manifest.inventor_id
            )
    if not manifest.checks:
        problems.append(
            "%s: local inventor must declare at least one check command"
            % manifest.inventor_id
        )
    for command in manifest.checks:
        if command[0] not in ("python", "python3"):
            problems.append(
                "%s: check command must use python or python3 without a shell"
                % manifest.inventor_id
            )
    return problems


def run_declared_checks(manifest: InventorManifest) -> List[str]:
    """Run one inventor's declared checks without shell interpolation."""

    problems = validate_contribution(manifest)
    if problems or manifest.source.get("kind") != "local":
        return problems
    root = manifest.path.parent
    workshop_src = Path(__file__).resolve().parents[2]
    paths = [str(workshop_src)]
    if (root / "src").is_dir():
        paths.append(str(root / "src"))
    paths.append(str(root))
    existing = os.environ.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for command in manifest.checks:
        executable = [sys.executable, *command[1:]]
        completed = subprocess.run(
            executable,
            cwd=str(root),
            env=environment,
            check=False,
        )
        if completed.returncode:
            problems.append(
                "%s: check failed (%s): %s"
                % (
                    manifest.inventor_id,
                    completed.returncode,
                    " ".join(command),
                )
            )
            break
    return problems


def manifests_for_target(target: Path) -> Sequence[InventorManifest]:
    """Resolve an inventor folder, manifest, repository, or collection."""

    # Keep paths absolute before loading manifests or starting subprocesses.
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

    Match owns routing cards and semantic selection. Contributors owns whether
    a collection contains complete, runnable inventor identities, which is the
    only fact atomic scaffolding needs before publication.
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
    entrypoint_problems = validate_entrypoints(manifests)
    if entrypoint_problems:
        raise ManifestError("; ".join(entrypoint_problems))
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
