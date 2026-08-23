"""Seal, inspect, and identify exact Pack bytes for a Door."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .artifacts import (
    ArtifactManifest,
    MAX_ENTRIES,
    MAX_EXPANDED_BYTES,
    MAX_FILE_BYTES,
    MAX_PACK_BYTES,
    _assert_path_has_no_secret,
    _validate_pack_limit,
    assert_packable_content,
    build_artifact_manifest,
    build_pack,
)
from .errors import ContractError
from .models import require_sha256


_OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", set())


def _safe_pack_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or not candidate.parts
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("Pack contains an unsafe member path")
    return value


def _read_pack_bytes(pack: Path) -> bytes:
    """Read one regular file while refusing replaced/symlinked path components."""
    # O_NONBLOCK prevents a regular-file-to-FIFO race from hanging before the
    # descriptor can be inspected and rejected.
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
    descriptor = None
    directory_descriptor = None
    try:
        expected_file = pack.lstat()
        expected_parent = pack.parent.stat()
    except (OSError, ValueError) as exc:
        raise ContractError(
            "cannot inspect Pack %s: %s" % (pack, exc)
        ) from exc
    if not stat.S_ISREG(expected_file.st_mode):
        raise ContractError(
            "Pack must be a regular non-symlink file: %s" % pack
        )
    try:
        if _OPEN_SUPPORTS_DIR_FD and hasattr(os, "O_DIRECTORY"):
            # Resolve an intentionally supplied parent alias once, then walk
            # the canonical path through descriptors. If any canonical parent
            # is swapped for a symlink between resolution and open, O_NOFOLLOW
            # rejects it instead of redirecting the bearer-bound upload.
            parent = pack.parent.resolve(strict=True)
            anchor = Path(parent.anchor)
            directory_descriptor = os.open(str(anchor), directory_flags)
            for part in parent.parts[1:]:
                child = os.open(part, directory_flags, dir_fd=directory_descriptor)
                os.close(directory_descriptor)
                directory_descriptor = child
            opened_parent = os.fstat(directory_descriptor)
            if (opened_parent.st_dev, opened_parent.st_ino) != (
                expected_parent.st_dev,
                expected_parent.st_ino,
            ):
                raise ContractError(
                    "Pack parent was replaced while opening: %s"
                    % pack.parent
                )
            descriptor = os.open(pack.name, flags, dir_fd=directory_descriptor)
            opened_file = os.fstat(descriptor)
            if (opened_file.st_dev, opened_file.st_ino) != (
                expected_file.st_dev,
                expected_file.st_ino,
            ):
                raise ContractError(
                    "Pack was replaced while opening: %s" % pack
                )
        else:
            parent = pack.parent.resolve(strict=True)
            resolved_parent = parent.stat()
            if (resolved_parent.st_dev, resolved_parent.st_ino) != (
                expected_parent.st_dev,
                expected_parent.st_ino,
            ):
                raise ContractError(
                    "Pack parent was replaced while opening: %s"
                    % pack.parent
                )
            descriptor = os.open(str(parent / pack.name), flags)
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (
                expected_file.st_dev,
                expected_file.st_ino,
            ):
                raise ContractError(
                    "Pack was replaced while opening: %s" % pack
                )
    except ContractError:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        raise
    except (OSError, ValueError) as exc:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        raise ContractError(
            "cannot safely open Pack %s: %s" % (pack, exc)
        ) from exc
    finally:
        if directory_descriptor is not None:
            os.close(directory_descriptor)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ContractError(
                "Pack must be a regular non-symlink file: %s" % pack
            )
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_PACK_BYTES:
                raise ContractError("Pack exceeds the 50 MB client limit")
        after = os.fstat(descriptor)
        if after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise ContractError("Pack changed while it was read: %s" % pack)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _validate_pack_bytes(content: bytes) -> Tuple[bytes, str, str]:
    """Verify immutable bytes as one exact canonical Workshop Pack."""
    if type(content) is not bytes:
        raise ContractError("Pack content must be immutable bytes")
    if len(content) > MAX_PACK_BYTES:
        raise ContractError("Pack exceeds the 50 MB client limit")
    pack_sha256 = hashlib.sha256(content).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.comment:
                raise ContractError("Pack must not contain a zip comment")
            if len(infos) > MAX_ENTRIES + 1 or len(names) != len(set(names)):
                raise ContractError("Pack has too many or duplicate members")
            for name in names:
                _safe_pack_path(name)
            if names.count("_inventor-artifact.json") != 1:
                raise ContractError("Pack needs exactly one Workshop artifact manifest")
            if any(info.is_dir() for info in infos):
                raise ContractError("Pack must contain files, not directory members")
            if any(
                info.compress_type != zipfile.ZIP_STORED
                or info.date_time != (1980, 1, 1, 0, 0, 0)
                or info.create_system != 3
                or info.extra
                or info.comment
                or info.flag_bits & 0x1
                for info in infos
            ):
                raise ContractError("Pack members are not in canonical Workshop form")
            if any(info.file_size > MAX_FILE_BYTES for info in infos):
                raise ContractError("Pack contains an oversized expanded file")
            if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
                raise ContractError("Pack exceeds the expanded-size limit")
            raw_manifest = json.loads(archive.read("_inventor-artifact.json").decode("utf-8"))
            if (
                not isinstance(raw_manifest, Mapping)
                or set(raw_manifest) != {
                    "schema_version",
                    "artifact_sha256",
                    "total_bytes",
                    "created_at",
                    "entries",
                }
                or type(raw_manifest.get("schema_version")) is not int
                or raw_manifest.get("schema_version") != 1
                or raw_manifest.get("created_at") != "content-addressed"
            ):
                raise ContractError("Pack artifact manifest is malformed")
            raw_entries = raw_manifest.get("entries")
            if not isinstance(raw_entries, list) or not raw_entries:
                raise ContractError("Pack artifact manifest has no entries")
            canonical_entries = []
            expected_names = []
            verified_members = {}
            total_bytes = 0
            info_by_name = {info.filename: info for info in infos}
            for raw in raw_entries:
                if not isinstance(raw, Mapping) or set(raw) != {
                    "path", "bytes", "sha256", "executable"
                }:
                    raise ContractError("Pack artifact entry is malformed")
                name = _safe_pack_path(raw.get("path")) if isinstance(raw.get("path"), str) else ""
                size = raw.get("bytes")
                digest = raw.get("sha256")
                executable = raw.get("executable")
                if (
                    not name
                    or name == "_inventor-artifact.json"
                    or not isinstance(size, int)
                    or isinstance(size, bool)
                    or size < 0
                    or not isinstance(executable, bool)
                ):
                    raise ContractError("Pack artifact entry has invalid fields")
                require_sha256(digest, "Pack entry sha256")
                if name in expected_names or name not in info_by_name:
                    raise ContractError("Pack manifest inventory does not match the zip")
                member = archive.read(name)
                assert_packable_content(name, member)
                if len(member) != size or hashlib.sha256(member).hexdigest() != digest:
                    raise ContractError("Pack member does not match its manifest")
                mode = (info_by_name[name].external_attr >> 16) & 0o777
                if mode != (0o755 if executable else 0o644):
                    raise ContractError("Pack permissions do not match its manifest")
                canonical_entries.append(
                    {"path": name, "bytes": size, "sha256": digest, "executable": executable}
                )
                verified_members[name] = member
                expected_names.append(name)
                total_bytes += size
            if expected_names != sorted(expected_names):
                raise ContractError("Pack manifest entries must be sorted")
            if set(names) != set(expected_names) | {"_inventor-artifact.json"}:
                raise ContractError("Pack has undeclared members")
            if (
                type(raw_manifest.get("total_bytes")) is not int
                or raw_manifest.get("total_bytes") != total_bytes
            ):
                raise ContractError("Pack manifest total_bytes is inconsistent")
            artifact_sha256 = hashlib.sha256(
                json.dumps(
                    canonical_entries,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
            if raw_manifest.get("artifact_sha256") != artifact_sha256:
                raise ContractError("Pack artifact identity is inconsistent")
            canonical_buffer = io.BytesIO()
            with zipfile.ZipFile(
                canonical_buffer, "w", compression=zipfile.ZIP_STORED
            ) as canonical_archive:
                for entry in canonical_entries:
                    name = entry["path"]
                    info = zipfile.ZipInfo(
                        name, date_time=(1980, 1, 1, 0, 0, 0)
                    )
                    info.compress_type = zipfile.ZIP_STORED
                    info.create_system = 3
                    info.external_attr = (
                        (0o755 if entry["executable"] else 0o644) & 0xFFFF
                    ) << 16
                    canonical_archive.writestr(
                        info,
                        verified_members[name],
                        compress_type=zipfile.ZIP_STORED,
                    )
                info = zipfile.ZipInfo(
                    "_inventor-artifact.json",
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o644 & 0xFFFF) << 16
                canonical_archive.writestr(
                    info,
                    json.dumps(
                        raw_manifest,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                    + b"\n",
                    compress_type=zipfile.ZIP_STORED,
                )
            if canonical_buffer.getvalue() != content:
                raise ContractError(
                    "Pack bytes are not the exact canonical Workshop ZIP"
                )
    except (OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Pack is not a valid Workshop zip: %s" % exc) from exc
    return content, pack_sha256, artifact_sha256


def _load_pack(pack: Path) -> Tuple[bytes, str, str]:
    """Read once, verify the Workshop manifest, and identify the exact upload bytes."""
    return _validate_pack_bytes(_read_pack_bytes(Path(pack)))


def _inspect_pack_details(pack: Path) -> Dict[str, Any]:
    """Validate a canonical Pack and return its content identity.

    This intentionally exposes identities and counts, not the Pack bytes.
    Uploads remain responsible for reading and validating the exact bytes at
    the effect boundary through a qualified Shop Door.
    """
    content, pack_sha256, artifact_sha256 = _load_pack(Path(pack))
    with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
        entries = len(archive.infolist())
    return {
        "bytes": len(content),
        "entries": entries,
        "pack_sha256": pack_sha256,
        "artifact_sha256": artifact_sha256,
    }


@dataclass(frozen=True, init=False)
class PackedArtifact:
    """One canonical immutable Pack ready to send through a Door."""

    path: Path
    bytes: int
    entries: int
    pack_sha256: str
    artifact_sha256: str

    def __init__(
        self,
        path: Path,
        bytes: int,
        entries: int,
        pack_sha256: str,
        artifact_sha256: str,
    ) -> None:
        """Validate caller-authored claims against the canonical Pack bytes."""

        self._set_claims(path, bytes, entries, pack_sha256, artifact_sha256)
        self.assert_valid()

    def _set_claims(
        self,
        path: Path,
        bytes: int,
        entries: int,
        pack_sha256: str,
        artifact_sha256: str,
    ) -> None:
        path = Path(path)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ContractError("PackedArtifact path must be an absolute regular file")
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise ContractError("cannot resolve PackedArtifact path") from exc
        if type(bytes) is not int or bytes <= 0:
            raise ContractError("PackedArtifact bytes must be a positive integer")
        if type(entries) is not int or entries < 2:
            raise ContractError("PackedArtifact entries must include content and manifest")
        require_sha256(pack_sha256, "PackedArtifact pack_sha256")
        require_sha256(artifact_sha256, "PackedArtifact artifact_sha256")
        object.__setattr__(self, "path", resolved)
        object.__setattr__(self, "bytes", bytes)
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "pack_sha256", pack_sha256)
        object.__setattr__(self, "artifact_sha256", artifact_sha256)

    @classmethod
    def _from_inspection(cls, path: Path, details: Mapping[str, object]) -> "PackedArtifact":
        instance = object.__new__(cls)
        instance._set_claims(
            path,
            details["bytes"],
            details["entries"],
            details["pack_sha256"],
            details["artifact_sha256"],
        )
        return instance

    def assert_valid(self) -> None:
        details = _inspect_pack_details(self.path)
        expected = {
            "bytes": self.bytes,
            "entries": self.entries,
            "pack_sha256": self.pack_sha256,
            "artifact_sha256": self.artifact_sha256,
        }
        if any(details[name] != value for name, value in expected.items()):
            raise ContractError("PackedArtifact claims do not match the Pack bytes")

    @property
    def packet_sha256(self) -> str:
        """Compatibility spelling used by Workshop 0.2."""

        return self.pack_sha256

    def to_dict(self) -> Mapping[str, object]:
        self.assert_valid()
        return {
            "path": str(self.path),
            "bytes": self.bytes,
            "entries": self.entries,
            "pack_sha256": self.pack_sha256,
            "artifact_sha256": self.artifact_sha256,
        }


@dataclass(frozen=True)
class PackPlan:
    """Exact, read-only size plan for one canonical Workshop Pack.

    A plan inventories and hashes eligible product files, but it does not
    create transport bytes or claim that later secret/content checks passed.
    It is intended for an inventor's Make/feedback loop before Pack.
    """

    artifact_sha256: str
    product_bytes: int
    pack_bytes: int
    entries: int
    limit_bytes: int
    largest_files: Tuple[Tuple[str, int], ...]

    def __post_init__(self) -> None:
        require_sha256(self.artifact_sha256, "Pack plan artifact_sha256")
        for value, label, minimum in (
            (self.product_bytes, "product_bytes", 0),
            (self.pack_bytes, "pack_bytes", 1),
            (self.entries, "entries", 2),
            (self.limit_bytes, "limit_bytes", 1),
        ):
            if type(value) is not int or value < minimum:
                raise ContractError("Pack plan %s is invalid" % label)
        if (
            not isinstance(self.largest_files, tuple)
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or type(item[1]) is not int
                or item[1] < 0
                for item in self.largest_files
            )
        ):
            raise ContractError("Pack plan largest_files is invalid")
        for path, _ in self.largest_files:
            _safe_pack_path(path)
            _assert_path_has_no_secret(path)
        if self.limit_bytes > MAX_PACK_BYTES:
            raise ContractError("Pack plan limit exceeds the canonical 50 MB limit")

    @property
    def fits(self) -> bool:
        return self.pack_bytes <= self.limit_bytes

    @property
    def over_by(self) -> int:
        return max(0, self.pack_bytes - self.limit_bytes)

    def to_dict(self) -> Mapping[str, object]:
        return {
            "schema_version": 1,
            "artifact_sha256": self.artifact_sha256,
            "product_bytes": self.product_bytes,
            "pack_bytes": self.pack_bytes,
            "entries": self.entries,
            "limit_bytes": self.limit_bytes,
            "fits": self.fits,
            "over_by": self.over_by,
            "largest_files": [
                {"path": path, "bytes": size}
                for path, size in self.largest_files
            ],
        }


def plan_pack(
    artifact_root: Path,
    *,
    extra_excludes: Iterable[str] = (),
    maximum_bytes: int = MAX_PACK_BYTES,
    largest: int = 5,
) -> PackPlan:
    """Return the exact canonical Pack size without writing a ZIP."""

    maximum_bytes = _validate_pack_limit(maximum_bytes)
    if type(largest) is not int or largest < 0 or largest > 100:
        raise ContractError("Pack plan largest must be an integer from 0 to 100")
    manifest = seal_artifact(
        artifact_root,
        created_at="content-addressed",
        extra_excludes=extra_excludes,
    )
    manifest_content = (
        json.dumps(
            manifest.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )
    members = [(entry.path, entry.bytes) for entry in manifest.entries]
    members.append(("_inventor-artifact.json", len(manifest_content)))
    pack_bytes = 22 + sum(
        size + 76 + 2 * len(path.encode("utf-8"))
        for path, size in members
    )
    biggest = tuple(
        (entry.path, entry.bytes)
        for entry in sorted(
            manifest.entries,
            key=lambda entry: (-entry.bytes, entry.path),
        )[:largest]
    )
    return PackPlan(
        artifact_sha256=manifest.artifact_sha256,
        product_bytes=manifest.total_bytes,
        pack_bytes=pack_bytes,
        entries=len(manifest.entries) + 1,
        limit_bytes=maximum_bytes,
        largest_files=biggest,
    )


def seal_artifact(
    artifact_root: Path,
    *,
    created_at: Optional[str] = None,
    extra_excludes: Iterable[str] = (),
) -> ArtifactManifest:
    """Create the content-addressed inventory used by Make and Inspect."""

    return build_artifact_manifest(
        artifact_root,
        created_at=created_at,
        extra_excludes=extra_excludes,
    )


def inspect_pack(path: Path) -> PackedArtifact:
    """Verify canonical ZIP bytes and return their identities."""

    requested = Path(path)
    if requested.is_symlink():
        raise ContractError("Pack path must not be a symlink")
    resolved = requested.resolve(strict=True)
    details = _inspect_pack_details(resolved)
    return PackedArtifact._from_inspection(resolved, details)


def pack_artifact(
    artifact_root: Path,
    destination: Path,
    *,
    extra_excludes: Iterable[str] = (),
    maximum_bytes: int = MAX_PACK_BYTES,
) -> PackedArtifact:
    """Build, atomically write, and re-inspect one canonical Pack."""

    build_pack(
        artifact_root,
        destination,
        extra_excludes=extra_excludes,
        maximum_bytes=maximum_bytes,
    )
    return inspect_pack(destination)
