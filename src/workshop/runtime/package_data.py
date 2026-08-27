"""Resolve validated, read-only data shipped inside the Workshop package.

Product runs copy exact Inventor and skill bytes directly into their persistent
project. This module only discovers and validates installed package data; it
never creates a second writable Inventor tree or executes contributor code.
"""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
from types import MappingProxyType
from typing import Mapping, Optional

from workshop.contributors.extensions import (
    MAX_EXTENSION_FILE_BYTES,
    load_inventor_extension_bundles,
)
from workshop.contributors.manifest import load_manifest
from workshop.errors import ManifestError, WorkshopError


BUNDLED_INVENTOR_IDS = ("abo", "alice", "bob", "eve", "ivy", "leo")
BUNDLED_INVENTOR_FILES = ("TASTE.md", "inventor.json")
_PRODUCT_RUN_DOMAIN_SKILL_PATHS = (
    ("cad", Path("make/skills/cad")),
    ("design-reference", Path("make/skills/design-reference")),
    ("image-to-cad", Path("make/skills/image-to-cad")),
    ("manual-design", Path("release/skills/manual-design")),
    ("step-parts", Path("make/skills/step-parts")),
)
PRODUCT_RUN_DOMAIN_SKILLS = tuple(
    name for name, _relative in _PRODUCT_RUN_DOMAIN_SKILL_PATHS
)
_MAX_BUNDLED_FILE_BYTES = 512 * 1024


class PackageDataError(WorkshopError):
    """Installed Workshop data is absent, malformed, or changed."""


def _workshop_package_root(package_file: Path) -> Path:
    package_path = Path(package_file).resolve()
    return next(
        (parent for parent in package_path.parents if parent.name == "workshop"),
        package_path.parent,
    )


def packaged_data_root(group: str, package_file: Path) -> Optional[Path]:
    """Return a component-owned package-data directory when it is present."""

    if group not in ("inventors", "schemas", "skills"):
        raise ValueError("unknown Workshop package-data group: %s" % group)
    package_root = _workshop_package_root(package_file)
    relative = {
        "inventors": Path("contributors/_inventors"),
        "schemas": Path("."),
        "skills": Path("make/skills"),
    }[group]
    candidate = package_root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_dir():
        return None
    if group == "schemas" and not (
        resolved / "artifacts" / "schemas" / "artifact-manifest.schema.json"
    ).is_file():
        return None
    return resolved


def product_run_domain_skill_roots(
    package_file: Optional[Path] = None,
) -> Mapping[str, Path]:
    """Return the exact component-owned skills exposed to a product run."""

    package_root = _workshop_package_root(
        Path(__file__) if package_file is None else Path(package_file)
    )
    selected: dict[str, Path] = {}
    for name, relative in _PRODUCT_RUN_DOMAIN_SKILL_PATHS:
        candidate = package_root / relative
        if candidate.is_symlink() or not candidate.is_dir():
            raise PackageDataError("missing product-run domain skill: %s" % name)
        skill_file = candidate / "SKILL.md"
        if skill_file.is_symlink() or not skill_file.is_file():
            raise PackageDataError("domain skill has no regular SKILL.md: %s" % name)
        selected[name] = candidate.resolve()
    return MappingProxyType(selected)


def _read_regular_payload(
    path: Path, *, maximum: int = _MAX_BUNDLED_FILE_BYTES
) -> tuple[bytes, int]:
    """Read one bounded package asset and normalize its executable mode."""

    try:
        before = path.lstat()
    except OSError as exc:
        raise PackageDataError("missing bundled Inventor file: %s" % path) from exc
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise PackageDataError("bundled Inventor file is not regular: %s" % path)
    if before.st_size < 1 or before.st_size > maximum:
        raise PackageDataError(
            "bundled Inventor file must contain 1 to %d bytes: %s"
            % (maximum, path)
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise PackageDataError("cannot open bundled Inventor file: %s" % path) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise PackageDataError("bundled Inventor file changed while opening: %s" % path)
        chunks = []
        observed = 0
        while True:
            chunk = os.read(
                descriptor,
                min(64 * 1024, maximum + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise PackageDataError("bundled Inventor file is too large: %s" % path)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise PackageDataError("bundled Inventor file changed while reading: %s" % path)
        mode = 0o500 if opened.st_mode & 0o111 else 0o400
        return b"".join(chunks), mode
    finally:
        os.close(descriptor)


def _inventor_payloads(root: Path) -> tuple[tuple[str, bytes, int], ...]:
    """Validate and snapshot exact schema-v8 identities and skill trees."""

    if root.is_symlink() or not root.is_dir():
        raise PackageDataError(
            "bundled Inventor root is not a regular directory: %s" % root
        )
    try:
        root_entries = tuple(root.iterdir())
    except OSError as exc:
        raise PackageDataError("cannot list bundled Inventor root: %s" % root) from exc
    observed_ids = set()
    for entry in root_entries:
        if entry.is_symlink() or not entry.is_dir():
            raise PackageDataError(
                "bundled Inventor root may contain only real directories: %s"
                % entry
            )
        observed_ids.add(entry.name)
    if observed_ids != set(BUNDLED_INVENTOR_IDS):
        raise PackageDataError("bundled Inventor inventory is invalid")

    payloads: list[tuple[str, bytes, int]] = []
    for inventor_id in BUNDLED_INVENTOR_IDS:
        folder = root / inventor_id
        if folder.is_symlink() or not folder.is_dir():
            raise PackageDataError("missing bundled Inventor folder: %s" % folder)
        try:
            children = tuple(folder.iterdir())
        except OSError as exc:
            raise PackageDataError(
                "cannot list bundled Inventor folder: %s" % folder
            ) from exc
        required = {"TASTE.md", "inventor.json", "skills"}
        observed = set()
        for child in children:
            if child.is_symlink():
                raise PackageDataError("bundled Inventor folder contains a symlink")
            observed.add(child.name)
        if observed != required:
            raise PackageDataError(
                "bundled Inventor folder differs from its schema-v8 inventory: %s"
                % folder
            )

        for filename in BUNDLED_INVENTOR_FILES:
            relative = "%s/%s" % (inventor_id, filename)
            content, mode = _read_regular_payload(folder / filename)
            if mode != 0o400:
                raise PackageDataError(
                    "bundled Inventor identity file must not be executable: %s"
                    % (folder / filename)
                )
            payloads.append((relative, content, mode))

        try:
            manifest = load_manifest(folder / "inventor.json")
            if manifest.schema_version != 8 or manifest.inventor_id != inventor_id:
                raise PackageDataError(
                    "bundled Inventors must use the native schema-v8 skill contract"
                )
            bundles = load_inventor_extension_bundles(manifest)
        except ManifestError as exc:
            raise PackageDataError(
                "bundled Inventor extension inventory is invalid: %s" % folder
            ) from exc
        if not bundles:
            raise PackageDataError(
                "bundled schema-v8 Inventor declares no Codex skill: %s" % folder
            )
        for bundle in bundles:
            for entry in bundle.manifest.entries:
                path = bundle.root.joinpath(*Path(entry.path).parts)
                content, mode = _read_regular_payload(
                    path, maximum=MAX_EXTENSION_FILE_BYTES
                )
                expected_mode = 0o500 if entry.executable else 0o400
                if mode != expected_mode:
                    raise PackageDataError(
                        "bundled Inventor skill mode differs from its manifest: %s"
                        % path
                    )
                relative = "%s/%s/%s" % (
                    inventor_id,
                    bundle.extension.path,
                    entry.path,
                )
                payloads.append((relative, content, mode))
    payloads.sort(key=lambda item: item[0])
    if len(payloads) != len({relative for relative, _, _ in payloads}):
        raise PackageDataError("bundled Inventor paths collide")
    return tuple(payloads)


def packaged_inventors_root(package_file: Optional[Path] = None) -> Optional[Path]:
    """Return the validated read-only Inventors embedded in an installed wheel.

    ``None`` means this is an editable/source layout with no embedded Inventors.
    A present but incomplete package is an installation error and fails closed.
    No contributor code is imported or executed during validation.
    """

    root = packaged_data_root(
        "inventors", Path(__file__) if package_file is None else Path(package_file)
    )
    if root is None:
        return None
    _inventor_payloads(root)
    return root


def default_workshop_home(environment: Optional[Mapping[str, str]] = None) -> Path:
    """Choose the user-owned state home without creating it."""

    values = os.environ if environment is None else environment
    configured = values.get("WORKSHOP_HOME")
    if configured:
        selected = Path(configured).expanduser()
        if not selected.is_absolute():
            raise PackageDataError("WORKSHOP_HOME must be an absolute path")
        return selected
    xdg = values.get("XDG_DATA_HOME")
    if xdg:
        selected = Path(xdg).expanduser()
        if not selected.is_absolute():
            raise PackageDataError("XDG_DATA_HOME must be an absolute path")
        return selected / "autonomous-workshop"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Autonomous Workshop"
    if os.name == "nt" and values.get("LOCALAPPDATA"):
        return Path(values["LOCALAPPDATA"]) / "Autonomous Workshop"
    return Path.home() / ".local" / "share" / "autonomous-workshop"
