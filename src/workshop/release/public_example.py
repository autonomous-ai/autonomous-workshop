"""Materialize one sanitized, public Git example from sealed Release bytes.

The private product-run workspace remains the lifecycle authority.  This
module writes only an allowlisted public projection after authenticated
Factory readback proves that the exact Release is public.  It never copies a
Wish, checkpoint, receipt, agent configuration, transcript, or evidence tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import urllib.parse
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - current Workshop hosts are POSIX
    fcntl = None  # type: ignore[assignment]

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError, StateConflict
from workshop.make.native import NativeMade
from workshop.release.native import NativeRelease
from workshop.runtime import Receipt


_PUBLIC_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PUBLIC_INVENTOR = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_PUBLIC_NAME = 100


def _canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("public example values must be finite JSON") from exc


def _real_directory(path: Path, label: str) -> Path:
    try:
        identity = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
        or resolved != path
    ):
        raise StateConflict("%s must be a canonical real directory" % label)
    return resolved


def _https_public_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise StateConflict("%s is not a bounded HTTPS URL" % label)
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise StateConflict("%s is not a bounded HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise StateConflict("%s is not a bounded HTTPS URL" % label)
    return value


def _bound_bytes(
    root: Path,
    entries: Mapping[str, Any],
    relative: str,
    *,
    label: str,
) -> bytes:
    entry = entries.get(relative)
    pure = PurePosixPath(relative)
    if entry is None or pure.is_absolute() or ".." in pure.parts:
        raise StateConflict("%s is not bound to the sealed artifact" % label)
    path = root.joinpath(*pure.parts)
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or len(content) != entry.bytes
        or hashlib.sha256(content).hexdigest() != entry.sha256
    ):
        raise StateConflict("%s differs from its sealed artifact binding" % label)
    return content


def _write_public_file(root: Path, relative: str, content: bytes) -> None:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
        raise ContractError("public example output path is invalid")
    target = root.joinpath(*pure.parts)
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            str(target),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
    except OSError as exc:
        raise StateConflict("public example output could not be created") from exc
    try:
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(target, 0o644)


def _install_staging_exclusively(
    staging: Path,
    *,
    parent_descriptor: int,
    target_name: str,
    target: Path,
) -> None:
    """Install a validated tree without replacing any concurrent path.

    POSIX ``rename`` may replace an empty destination directory, even after an
    absence check.  Reserve the public directory with an exclusive ``mkdir``
    and populate it through no-follow directory descriptors plus ``O_EXCL``
    files instead.  A crash can leave a partial directory, which intentionally
    becomes a hard collision for later review; no existing byte is overwritten.
    """

    os.mkdir(target_name, mode=0o755, dir_fd=parent_descriptor)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_descriptor = os.open(
        target_name,
        directory_flags,
        dir_fd=parent_descriptor,
    )
    root_identity = os.fstat(root_descriptor)
    opened: dict[tuple[str, ...], int] = {(): root_descriptor}
    try:
        files, directories = _tree_inventory(staging)
        for relative in sorted(
            directories,
            key=lambda value: (len(PurePosixPath(value).parts), value),
        ):
            pure = PurePosixPath(relative)
            parent_parts = pure.parts[:-1]
            parent = opened.get(parent_parts)
            if parent is None:
                raise StateConflict("public example directory order is invalid")
            os.mkdir(pure.name, mode=0o755, dir_fd=parent)
            opened[pure.parts] = os.open(
                pure.name,
                directory_flags,
                dir_fd=parent,
            )

        for relative in files:
            pure = PurePosixPath(relative)
            parent = opened.get(pure.parts[:-1])
            if parent is None:
                raise StateConflict("public example file parent is invalid")
            source = staging.joinpath(*pure.parts)
            try:
                before = source.lstat()
                content = source.read_bytes()
                after = source.lstat()
            except OSError as exc:
                raise StateConflict(
                    "public example staging file is unavailable"
                ) from exc
            if (
                source.is_symlink()
                or not stat.S_ISREG(before.st_mode)
                or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
                != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
            ):
                raise StateConflict("public example staging file changed")
            descriptor = os.open(
                pure.name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o644,
                dir_fd=parent,
            )
            try:
                written = 0
                while written < len(content):
                    written += os.write(descriptor, content[written:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

        for parts, descriptor in sorted(
            opened.items(), key=lambda item: len(item[0]), reverse=True
        ):
            del parts
            os.fsync(descriptor)
        os.fsync(parent_descriptor)
    finally:
        for descriptor in set(opened.values()):
            try:
                os.close(descriptor)
            except OSError:
                pass

    try:
        installed = target.lstat()
    except OSError as exc:
        raise StateConflict("public example installation disappeared") from exc
    if (
        target.is_symlink()
        or not stat.S_ISDIR(installed.st_mode)
        or (installed.st_dev, installed.st_ino)
        != (root_identity.st_dev, root_identity.st_ino)
        or not _trees_are_identical(target, staging)
    ):
        raise StateConflict("public example installation changed concurrently")


def _tree_inventory(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    files = []
    directories = []
    try:
        entries = sorted(root.rglob("*"), key=lambda item: item.as_posix())
    except OSError as exc:
        raise StateConflict("public example tree cannot be inventoried") from exc
    for entry in entries:
        relative = entry.relative_to(root).as_posix()
        try:
            identity = entry.lstat()
        except OSError as exc:
            raise StateConflict("public example tree changed while reading") from exc
        if entry.is_symlink():
            raise StateConflict("public example tree may not contain symlinks")
        if stat.S_ISDIR(identity.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(identity.st_mode):
            files.append(relative)
        else:
            raise StateConflict("public example tree contains a special file")
    return tuple(files), tuple(directories)


def _trees_are_identical(left: Path, right: Path) -> bool:
    left_files, left_directories = _tree_inventory(left)
    right_files, right_directories = _tree_inventory(right)
    if left_files != right_files or left_directories != right_directories:
        return False
    for relative in left_files:
        left_path = left.joinpath(*PurePosixPath(relative).parts)
        right_path = right.joinpath(*PurePosixPath(relative).parts)
        if left_path.read_bytes() != right_path.read_bytes():
            return False
    return True


def _copy_model(
    *,
    product_root: Path,
    product_entries: Mapping[str, Any],
    source: str,
    destination: str,
    staging: Path,
) -> dict[str, Any]:
    content = _bound_bytes(
        product_root,
        product_entries,
        source,
        label="public model %s" % source,
    )
    _write_public_file(staging, destination, content)
    return {
        "path": destination,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def materialize_public_example(
    repository_root: Path,
    run_root: Path,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
) -> Path:
    """Create ``toys/<inventor>-<slug>`` from exact public Release bytes.

    Repeating the operation with identical bytes is idempotent.  An existing
    symlink, partial directory, or different snapshot is a hard collision; no
    public example is overwritten or merged.
    """

    if not isinstance(release, NativeRelease) or not isinstance(made, NativeMade):
        raise ContractError("public example requires typed Made and Release inputs")
    if not isinstance(receipt, Receipt) or not receipt.is_verified_public:
        raise StateConflict("public example requires verified public Factory readback")
    if (
        not isinstance(inventor_id, str)
        or len(inventor_id) > _MAX_PUBLIC_NAME
        or _PUBLIC_INVENTOR.fullmatch(inventor_id) is None
    ):
        raise ContractError("public example Inventor id is not a canonical slug")
    slug = receipt.slug
    if (
        not isinstance(slug, str)
        or len(slug) > _MAX_PUBLIC_NAME
        or _PUBLIC_SLUG.fullmatch(slug) is None
    ):
        raise StateConflict("public Factory slug is not safe for a repository path")
    receipt.assert_artifact(release.product_artifact_sha256)
    details = receipt.details
    for field in (
        "factory_content_sha256",
        "manual_sha256",
        "primary_model_sha256",
        "product_page_sha256",
        "release_sha256",
    ):
        if (
            not isinstance(details.get(field), str)
            or re.fullmatch(r"[0-9a-f]{64}", details[field]) is None
        ):
            raise StateConflict("public Factory receipt lacks exact byte identities")
    if (
        release.made_sha256 != made.made_sha256
        or release.product_artifact_sha256
        != made.product_manifest.artifact_sha256
        or details.get("release_sha256")
        != release.package_manifest.artifact_sha256
        or details.get("product_page_sha256") != release.product_json_sha256
    ):
        raise StateConflict("public Factory receipt belongs to different Release bytes")

    repository = _real_directory(Path(repository_root), "Workshop repository")
    run = _real_directory(Path(run_root), "private run workspace")
    toys = _real_directory(repository / "toys", "public examples directory")
    package_root = _real_directory(
        run.joinpath(*PurePosixPath(release.package_root).parts),
        "sealed Release package",
    )
    if build_artifact_manifest(
        package_root, created_at=release.package_manifest.created_at
    ).to_dict() != release.package_manifest.to_dict():
        raise StateConflict("sealed Release package differs from its manifest")
    made_product = made.validate_product_tree(run)
    product_root = _real_directory(
        made_product.artifact_root, "sealed Made product"
    )
    package_entries = {
        entry.path: entry for entry in release.package_manifest.entries
    }
    product_entries = {
        entry.path: entry for entry in made.product_manifest.entries
    }
    manual = _bound_bytes(
        package_root,
        package_entries,
        release.manual_path,
        label="public MANUAL.md",
    )
    product_json = _bound_bytes(
        package_root,
        package_entries,
        release.product_json_path,
        label="public product.json",
    )
    manual_entry = package_entries[release.manual_path]
    if details.get("manual_sha256") != manual_entry.sha256:
        raise StateConflict("public Factory receipt belongs to different manual bytes")

    target = toys / (inventor_id + "-" + slug)
    staging = Path(
        tempfile.mkdtemp(prefix=".public-example-", dir=str(toys))
    ).resolve(strict=True)
    try:
        _write_public_file(staging, "MANUAL.md", manual)
        _write_public_file(staging, "product.json", product_json)

        print_files = []
        primary_model = None
        primary_path = details.get("primary_model_path")
        primary_sha256 = details.get("primary_model_sha256")
        cad = made.product.get("cad")
        assembled_reference = (
            cad.get("assembled_stl") if isinstance(cad, Mapping) else None
        )
        if isinstance(assembled_reference, Mapping):
            if (
                assembled_reference.get("path") != primary_path
                or assembled_reference.get("sha256") != primary_sha256
            ):
                raise StateConflict(
                    "public Factory primary model differs from Made product facts"
                )
        if (
            isinstance(primary_path, str)
            and PurePosixPath(primary_path).suffix.casefold() == ".stl"
        ):
            entry = product_entries.get(primary_path)
            if entry is None or entry.sha256 != primary_sha256:
                raise StateConflict(
                    "public Factory primary model differs from sealed Made bytes"
                )
            destination = "model/assembled.stl"
            primary_model = _copy_model(
                product_root=product_root,
                product_entries=product_entries,
                source=primary_path,
                destination=destination,
                staging=staging,
            )

        inventory = made.product.get("inventory")
        inventory_parts = (
            inventory.get("parts") if isinstance(inventory, Mapping) else None
        )
        if inventory_parts is not None and (
            not isinstance(inventory_parts, (list, tuple))
            or not inventory_parts
        ):
            raise StateConflict("Made product print inventory is malformed")
        for index, part in enumerate(inventory_parts or (), start=1):
            if not isinstance(part, Mapping):
                raise StateConflict("Made product print inventory is malformed")
            reference = part.get("stl")
            quantity = part.get("quantity")
            if (
                not isinstance(reference, Mapping)
                or type(quantity) is not int
                or not 1 <= quantity <= 10_000
            ):
                raise StateConflict("Made product print inventory is malformed")
            source = reference.get("path")
            if not isinstance(source, str):
                raise StateConflict("Made product print inventory is malformed")
            pure = PurePosixPath(source)
            entry = product_entries.get(source)
            if (
                pure.is_absolute()
                or pure.suffix.casefold() != ".stl"
                or ".." in pure.parts
                or entry is None
                or reference.get("bytes") != entry.bytes
                or reference.get("sha256") != entry.sha256
            ):
                raise StateConflict(
                    "Made product print inventory differs from sealed model bytes"
                )
            destination = "print/component-%03d.stl" % index
            copied = _copy_model(
                product_root=product_root,
                product_entries=product_entries,
                source=source,
                destination=destination,
                staging=staging,
            )
            copied["quantity"] = quantity
            print_files.append(copied)

        page_url = _https_public_url(details.get("page_url"), "public page URL")
        cover_url = _https_public_url(details.get("cover_url"), "public cover URL")
        title = str(release.product["title"])
        summary = str(release.product["summary"])
        publication = {
            "schema_version": 1,
            "kind": "autonomous-workshop.public-toy-snapshot",
            "title": title,
            "inventor": {"id": inventor_id},
            "publication": {
                "adapter": "factory",
                "status": "public",
                "slug": slug,
                "page_url": page_url,
                "cover_url": cover_url,
                "observed_at": receipt.observed_at,
                "listing": {
                    "price_cents": receipt.listing_price_cents,
                    "currency": receipt.listing_currency,
                },
            },
            "identities": {
                "native_release_sha256": release.release_sha256,
                "package_artifact_sha256": release.package_manifest.artifact_sha256,
                "product_artifact_sha256": release.product_artifact_sha256,
                "playtest_evidence_sha256": (
                    release.playtest_evidence_artifact_sha256
                ),
                "product_page_sha256": release.product_json_sha256,
                "manual_sha256": manual_entry.sha256,
                "factory_content_sha256": details.get("factory_content_sha256"),
                "primary_model_sha256": primary_sha256,
            },
            "primary_model": primary_model,
            "print_files": print_files,
        }
        _write_public_file(
            staging, "PUBLICATION.json", _canonical_json(publication)
        )
        heading = " ".join(title.split())
        readme = (
            "# %s\n\n%s\n\n"
            "[View the verified public product page](%s)\n\n"
            "## Snapshot contents\n\n"
            "- `product.json` — the exact sealed public Release page contract.\n"
            "- `MANUAL.md` — the exact sealed public manual.\n"
            "- `PUBLICATION.json` — sanitized public readback and byte identities.\n"
            "%s%s\n"
            "This snapshot contains no private Wish, agent session, host state, "
            "credentials, raw receipt, or internal evidence tree. Publication is "
            "not proof of physical manufacture, fit, durability, or delivery.\n"
        ) % (
            heading,
            summary,
            page_url,
            (
                "- `model/` — the exact public primary STL.\n"
                if primary_model is not None
                else ""
            ),
            (
                "- `print/` — exact sealed printable component STLs.\n"
                if print_files
                else ""
            ),
        )
        _write_public_file(staging, "README.md", readme.encode("utf-8"))
        for directory in sorted(
            (entry for entry in staging.rglob("*") if entry.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o755)
        os.chmod(staging, 0o755)

        if fcntl is None:
            raise StateConflict("public example publication requires POSIX locking")
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        directory_descriptor = os.open(str(toys), flags)
        try:
            fcntl.flock(directory_descriptor, fcntl.LOCK_EX)
            if target.exists() or target.is_symlink():
                existing = _real_directory(target, "existing public example")
                if _trees_are_identical(existing, staging):
                    return existing
                raise StateConflict(
                    "public example already exists with different or partial bytes"
                )
            try:
                _install_staging_exclusively(
                    staging,
                    parent_descriptor=directory_descriptor,
                    target_name=target.name,
                    target=target,
                )
            except OSError as exc:
                raise StateConflict(
                    "public example could not be installed without overwrite"
                ) from exc
        finally:
            try:
                fcntl.flock(directory_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(directory_descriptor)
        return target
    except (ArtifactError, OSError) as exc:
        raise StateConflict("public example materialization failed") from exc
    finally:
        if staging.exists() and staging != target:
            try:
                shutil.rmtree(staging)
            except OSError:
                pass


def materialize_public_example_if_source_checkout(
    repository_root: Optional[Path],
    run_root: Path,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
) -> Optional[Path]:
    """Materialize a public example when the host is running from a checkout."""

    if repository_root is None:
        return None
    return materialize_public_example(
        repository_root,
        run_root,
        release=release,
        made=made,
        inventor_id=inventor_id,
        receipt=receipt,
    )


__all__ = [
    "materialize_public_example",
    "materialize_public_example_if_source_checkout",
]
