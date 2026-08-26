"""Resolve filesystem-backed data shipped inside the Workshop package.

Schemas and skills are read in place. Bundled Inventors are different: their
Workshop runs create durable state, so an installed catalog must first be
copied byte-for-byte out of ``site-packages`` into a user-writable,
content-addressed home. Discovery in this module only reads identity files; it
never imports or executes a profile.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from types import MappingProxyType
from typing import Mapping, Optional

from workshop.errors import WorkshopError


BUNDLED_INVENTOR_IDS = ("alice", "bob", "eve", "ivy", "leo")
BUNDLED_INVENTOR_FILES = ("TASTE.md", "inventor.json", "profile.py")
PRODUCT_RUN_DOMAIN_SKILLS = ("cad", "product-to-cad", "step-parts")
_MAX_BUNDLED_FILE_BYTES = 512 * 1024
_CATALOG_HASH_DOMAIN = b"autonomous-workshop-bundled-inventors-v1\0"


class PackageDataError(WorkshopError):
    """Installed Workshop data is absent, malformed, or changed."""


def packaged_data_root(group: str, package_file: Path) -> Optional[Path]:
    """Return a component-owned package-data directory when it is present."""

    if group not in ("inventors", "schemas", "skills"):
        raise ValueError("unknown Workshop package-data group: %s" % group)
    package_path = Path(package_file).resolve()
    package_root = next(
        (parent for parent in package_path.parents if parent.name == "workshop"),
        package_path.parent,
    )
    relative = {
        "inventors": Path("contributors/_catalog/inventors"),
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

    root = packaged_data_root(
        "skills", Path(__file__) if package_file is None else Path(package_file)
    )
    if root is None:
        raise PackageDataError("this Workshop installation has no Make skills")
    selected: dict[str, Path] = {}
    for name in PRODUCT_RUN_DOMAIN_SKILLS:
        candidate = root / name
        if candidate.is_symlink() or not candidate.is_dir():
            raise PackageDataError("missing product-run domain skill: %s" % name)
        skill_file = candidate / "SKILL.md"
        if skill_file.is_symlink() or not skill_file.is_file():
            raise PackageDataError("domain skill has no regular SKILL.md: %s" % name)
        selected[name] = candidate.resolve()
    return MappingProxyType(selected)


def _read_regular_bytes(path: Path) -> bytes:
    """Read one bounded package asset without following a final symlink."""

    try:
        before = path.lstat()
    except OSError as exc:
        raise PackageDataError("missing bundled Inventor file: %s" % path) from exc
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise PackageDataError("bundled Inventor file is not regular: %s" % path)
    if before.st_size < 1 or before.st_size > _MAX_BUNDLED_FILE_BYTES:
        raise PackageDataError(
            "bundled Inventor file must contain 1 to %d bytes: %s"
            % (_MAX_BUNDLED_FILE_BYTES, path)
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
                min(64 * 1024, _MAX_BUNDLED_FILE_BYTES + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > _MAX_BUNDLED_FILE_BYTES:
                raise PackageDataError("bundled Inventor file is too large: %s" % path)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise PackageDataError("bundled Inventor file changed while reading: %s" % path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _catalog_payloads(root: Path) -> tuple[tuple[str, bytes], ...]:
    """Validate and snapshot the five package-owned Inventor identities."""

    if root.is_symlink() or not root.is_dir():
        raise PackageDataError("bundled Inventor catalog is not a regular directory: %s" % root)
    payloads = []
    for inventor_id in BUNDLED_INVENTOR_IDS:
        folder = root / inventor_id
        if folder.is_symlink() or not folder.is_dir():
            raise PackageDataError("missing bundled Inventor folder: %s" % folder)
        for filename in BUNDLED_INVENTOR_FILES:
            relative = "%s/%s" % (inventor_id, filename)
            payloads.append((relative, _read_regular_bytes(folder / filename)))
    return tuple(payloads)


def packaged_inventors_root(package_file: Optional[Path] = None) -> Optional[Path]:
    """Return the validated read-only catalog embedded in an installed wheel.

    ``None`` means this is an editable/source layout with no embedded catalog.
    A present but incomplete package is an installation error and fails closed.
    No profile code is imported during validation.
    """

    root = packaged_data_root(
        "inventors", Path(__file__) if package_file is None else Path(package_file)
    )
    if root is None:
        return None
    _catalog_payloads(root)
    return root


def packaged_inventor_catalog_root(
    package_file: Optional[Path] = None,
) -> Optional[Path]:
    """Return the read-only package root containing ``inventors/``.

    Read-only commands can pass this directly to catalog discovery without
    initializing user state. A Wish must use :func:`materialize_bundled_inventors`
    before writing its Manager assignment or Workshop database.
    """

    collection = packaged_inventors_root(package_file)
    return None if collection is None else collection.parent


def _payloads_sha256(payloads: tuple[tuple[str, bytes], ...]) -> str:
    digest = hashlib.sha256(_CATALOG_HASH_DOMAIN)
    for relative, payload in payloads:
        name = relative.encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def bundled_inventors_sha256(root: Path) -> str:
    """Bind every expected path and byte of a bundled Inventor catalog."""

    return _payloads_sha256(_catalog_payloads(Path(root)))


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


def _assert_materialized_catalog(root: Path, expected: tuple[tuple[str, bytes], ...]) -> None:
    actual = dict(_catalog_payloads(root / "inventors"))
    if actual != dict(expected):
        raise PackageDataError(
            "materialized bundled Inventor catalog differs from its installed package: %s"
            % root
        )


def materialize_bundled_inventors(
    destination: Optional[Path] = None,
    *,
    package_file: Optional[Path] = None,
) -> Path:
    """Return a writable catalog root containing exact installed identities.

    The returned path contains an ``inventors/`` collection and is keyed by all
    identity bytes. Existing files are never overwritten. Inventor runtime state
    may therefore live below this user-owned root without touching
    ``site-packages``.
    """

    source = packaged_inventors_root(package_file)
    if source is None:
        raise PackageDataError("this Workshop installation has no bundled Inventor catalog")
    payloads = _catalog_payloads(source)
    catalog_sha256 = _payloads_sha256(payloads)
    base = (
        default_workshop_home() / "bundled-catalogs"
        if destination is None
        else Path(destination)
    )
    if base.exists() and (base.is_symlink() or not base.is_dir()):
        raise PackageDataError("bundled catalog home must be a regular directory: %s" % base)
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = base / catalog_sha256
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            raise PackageDataError(
                "bundled catalog target is not a regular directory: %s" % target
            )
        _assert_materialized_catalog(target, payloads)
        return target

    staging = Path(tempfile.mkdtemp(prefix=".%s-" % catalog_sha256[:12], dir=base))
    try:
        collection = staging / "inventors"
        collection.mkdir()
        for relative, payload in payloads:
            output = collection / relative
            output.parent.mkdir(exist_ok=True)
            output.write_bytes(payload)
            output.chmod(0o444)
        _assert_materialized_catalog(staging, payloads)
        try:
            staging.rename(target)
        except OSError:
            if not target.is_dir() or target.is_symlink():
                raise
            _assert_materialized_catalog(target, payloads)
        return target
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def retained_bundled_catalog_roots(
    destination: Optional[Path] = None,
    *,
    package_file: Optional[Path] = None,
    materialize_current: bool = True,
) -> tuple[Path, ...]:
    """Return current then retained catalogs for exact status/resume lookup.

    A package upgrade gets a new content-addressed root. Older roots and their
    ``.workshop`` state remain in place so callers can resume against the exact
    Taste, manifest, and profile bytes that began a Wish. This function never
    migrates state to the current identity and never imports profile code.
    """

    if type(materialize_current) is not bool:
        raise TypeError("materialize_current must be a bool")
    packaged = packaged_inventors_root(package_file)
    if packaged is None:
        if materialize_current:
            raise PackageDataError(
                "this Workshop installation has no bundled Inventor catalog"
            )
        return ()
    current_sha256 = bundled_inventors_sha256(packaged)
    base = (
        default_workshop_home() / "bundled-catalogs"
        if destination is None
        else Path(destination)
    )
    if materialize_current:
        current = materialize_bundled_inventors(
            base, package_file=package_file
        )
    else:
        current = base / current_sha256
        if not base.exists():
            return ()
        if base.is_symlink() or not base.is_dir():
            raise PackageDataError(
                "bundled catalog home must be a regular directory: %s" % base
            )
    retained = []
    try:
        entries = tuple(base.iterdir())
    except OSError as exc:
        raise PackageDataError("cannot list retained bundled catalogs") from exc
    for candidate in entries:
        if candidate.is_symlink() or not candidate.is_dir():
            continue
        if len(candidate.name) != 64 or any(
            character not in "0123456789abcdef" for character in candidate.name
        ):
            continue
        payloads = _catalog_payloads(candidate / "inventors")
        if _payloads_sha256(payloads) != candidate.name:
            raise PackageDataError(
                "retained bundled catalog identity does not match its path: %s"
                % candidate
            )
        retained.append(candidate)
    return tuple(
        sorted(
            retained,
            key=lambda item: (item != current, item.name),
        )
    )


def existing_bundled_catalog_roots(
    destination: Optional[Path] = None,
    *,
    package_file: Optional[Path] = None,
) -> tuple[Path, ...]:
    """Enumerate exact installed catalog generations without creating state."""

    return retained_bundled_catalog_roots(
        destination,
        package_file=package_file,
        materialize_current=False,
    )
