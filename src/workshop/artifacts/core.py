"""Content-addressed artifact manifests and deterministic Packs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from workshop.errors import ArtifactError
from workshop._validation import require_sha256, require_utc_timestamp, utc_now

DEFAULT_EXCLUDED_DIRS = frozenset(
    (
        ".git",
        ".claude",
        ".idea",
        ".vscode",
        "__macosx",
        "__pycache__",
        "inputs",
        "transcripts",
    )
)
DEFAULT_EXCLUDED_FILES = frozenset(
    (
        ".ds_store",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "_inventor-artifact.json",
        "_tree.json",
        "auth.json",
        "catalog-auth.json",
        "credential.json",
        "credentials.json",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa",
        "panda-auth.json",
        "portal-auth.json",
        "access-token.json",
        "refresh-token.json",
        "token",
        "token.json",
        "token.txt",
        "tokens.json",
        "conversation_transcript.txt",
    )
)
DEFAULT_EXCLUDED_SUFFIXES = (
    ".backup",
    ".bak",
    ".db",
    ".db-journal",
    ".db-shm",
    ".db-wal",
    ".jsonl",
    ".key",
    ".pem",
    ".pyc",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite-journal",
    ".sqlite3",
    ".sqlite3-shm",
    ".sqlite3-wal",
    ".sqlite3-journal",
)
DEFAULT_EXCLUDED_PREFIXES = (".env", "auth.", "credential.", "credentials.", "secrets.")
MAX_ENTRIES = 4096
MAX_PACK_BYTES = 50 * 1024 * 1024
MAX_FILE_BYTES = 95 * 1024 * 1024
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
SECRET_PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "anthropic-key": re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai-key": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "google-api-key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "telegram-token": re.compile(rb"(?<![A-Za-z0-9])[0-9]{7,12}:[A-Za-z0-9_-]{30,}"),
    "credentialed-mongodb-uri": re.compile(rb"mongodb(?:\+srv)?://[^\s:/]+:[^\s/@]+@"),
}
_OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", set())
_ANCHORED_STAGING = (
    os.name != "nt"
    and _OPEN_SUPPORTS_DIR_FD
    and hasattr(os, "O_DIRECTORY")
    and all(
        operation in getattr(os, "supports_dir_fd", set())
        for operation in (os.mkdir, os.rmdir, os.stat, os.unlink)
    )
)


def _has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _assert_path_has_no_secret(relative_path: str) -> None:
    """Reject credential-shaped paths without echoing their sensitive bytes."""

    encoded_path = relative_path.encode("utf-8")
    for rule, pattern in SECRET_PATTERNS.items():
        if pattern.search(encoded_path):
            raise ArtifactError(
                "artifact filename matches secret rule %s" % rule
            )


def _validate_pack_limit(maximum_bytes: int) -> int:
    """Validate an optional lower ceiling against the canonical Pack limit."""

    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ArtifactError("Pack limit must be a positive integer")
    if maximum_bytes > MAX_PACK_BYTES:
        raise ArtifactError(
            "Pack limit cannot exceed the canonical 50 MB limit (%d bytes)"
            % MAX_PACK_BYTES
        )
    return maximum_bytes


def _open_regular_no_follow(root: Path, relative: Path) -> Tuple[int, os.stat_result]:
    """Resolve every path component through no-follow directory descriptors."""
    label = relative.as_posix()
    # A path can be exchanged for a FIFO between discovery and open.  Opening
    # nonblocking lets us fstat and reject that non-regular object instead of
    # hanging an autonomous worker forever waiting for a writer.
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
    try:
        expected_root = root.stat()
        expected_file = (root / relative).lstat()
    except OSError as exc:
        raise ArtifactError(
            "cannot inspect artifact file %s: %s" % (label, exc)
        ) from exc
    if not stat.S_ISDIR(expected_root.st_mode):
        raise ArtifactError("artifact root is not a directory: %s" % root)
    if not stat.S_ISREG(expected_file.st_mode):
        raise ArtifactError("artifact entry is not a regular file: %s" % label)
    if _OPEN_SUPPORTS_DIR_FD and hasattr(os, "O_DIRECTORY"):
        directory_descriptor = None
        try:
            directory_descriptor = os.open(str(root), directory_flags)
            opened_root = os.fstat(directory_descriptor)
            if (opened_root.st_dev, opened_root.st_ino) != (
                expected_root.st_dev,
                expected_root.st_ino,
            ):
                raise ArtifactError(
                    "artifact root was replaced while opening: %s" % root
                )
            for part in relative.parts[:-1]:
                child = os.open(part, directory_flags, dir_fd=directory_descriptor)
                os.close(directory_descriptor)
                directory_descriptor = child
            descriptor = os.open(
                relative.parts[-1], flags, dir_fd=directory_descriptor
            )
        except OSError as exc:
            raise ArtifactError(
                "cannot safely open artifact file %s: %s" % (label, exc)
            ) from exc
        finally:
            if directory_descriptor is not None:
                os.close(directory_descriptor)
    else:
        path = root / relative
        try:
            descriptor = os.open(str(path), flags)
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (
                expected_file.st_dev,
                expected_file.st_ino,
            ):
                raise ArtifactError("artifact file was replaced while opening: %s" % label)
        except Exception:
            if "descriptor" in locals():
                os.close(descriptor)
            raise
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ArtifactError("artifact entry is not a regular file: %s" % label)
        if (opened.st_dev, opened.st_ino) != (
            expected_file.st_dev,
            expected_file.st_ino,
        ):
            raise ArtifactError("artifact file was replaced while opening: %s" % label)
        return descriptor, opened
    except Exception:
        os.close(descriptor)
        raise


def _hash_open_file(root: Path, relative: Path) -> Tuple[str, os.stat_result]:
    descriptor, opened = _open_regular_no_follow(root, relative)
    try:
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise ArtifactError(
                "artifact changed while it was being hashed: %s" % relative.as_posix()
            )
        return digest.hexdigest(), after
    finally:
        os.close(descriptor)


def _read_open_file(root: Path, relative: Path) -> Tuple[bytes, os.stat_result]:
    descriptor, opened = _open_regular_no_follow(root, relative)
    try:
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise ArtifactError(
                "artifact changed while it was being read: %s" % relative.as_posix()
            )
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


@dataclass
class _PackStaging:
    """One held temporary inode, optionally under descriptor-anchored parents."""

    fd: int
    identity: os.stat_result
    parent: Path
    parent_identity: os.stat_result
    destination_name: str
    path: Optional[str] = None
    parent_fd: Optional[int] = None
    staging_fd: Optional[int] = None
    staging_name: Optional[str] = None
    member_name: Optional[str] = None

    @classmethod
    def create(cls, parent: Path, destination_name: str) -> "_PackStaging":
        parent_identity = parent.stat()
        if _ANCHORED_STAGING:
            parent_fd = None
            staging_fd = None
            staging_name = None
            fd = None
            member_name = None
            try:
                directory_flags = (
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0)
                )
                parent_fd = os.open(str(parent), directory_flags)
                opened_parent = os.fstat(parent_fd)
                if (opened_parent.st_dev, opened_parent.st_ino) != (
                    parent_identity.st_dev,
                    parent_identity.st_ino,
                ):
                    raise ArtifactError(
                        "Pack destination parent was replaced"
                    )
                for _ in range(32):
                    candidate = ".%s.stage-%s" % (
                        destination_name,
                        secrets.token_hex(12),
                    )
                    try:
                        os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                    except FileExistsError:
                        continue
                    staging_name = candidate
                    break
                if staging_name is None:
                    raise ArtifactError(
                        "cannot allocate private Pack staging"
                    )
                staging_fd = os.open(
                    staging_name, directory_flags, dir_fd=parent_fd
                )
                os.fchmod(staging_fd, 0o700)
                member_name = "pack.tmp"
                flags = (
                    os.O_RDWR
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0)
                )
                fd = os.open(member_name, flags, 0o600, dir_fd=staging_fd)
                identity = os.fstat(fd)
                return cls(
                    fd=fd,
                    identity=identity,
                    parent=parent,
                    parent_identity=parent_identity,
                    destination_name=destination_name,
                    parent_fd=parent_fd,
                    staging_fd=staging_fd,
                    staging_name=staging_name,
                    member_name=member_name,
                )
            except Exception:
                if fd is not None:
                    os.close(fd)
                if staging_fd is not None and member_name is not None:
                    try:
                        os.unlink(member_name, dir_fd=staging_fd)
                    except OSError:
                        pass
                if staging_fd is not None:
                    os.close(staging_fd)
                if parent_fd is not None and staging_name is not None:
                    try:
                        os.rmdir(staging_name, dir_fd=parent_fd)
                    except OSError:
                        pass
                if parent_fd is not None:
                    os.close(parent_fd)
                raise

        fd, path = tempfile.mkstemp(
            prefix=".%s." % destination_name, dir=str(parent)
        )
        identity = os.fstat(fd)
        current_parent = parent.stat()
        if (current_parent.st_dev, current_parent.st_ino) != (
            parent_identity.st_dev,
            parent_identity.st_ino,
        ):
            os.close(fd)
            try:
                os.unlink(path)
            except OSError:
                pass
            raise ArtifactError("Pack destination parent was replaced")
        return cls(
            fd=fd,
            identity=identity,
            parent=parent,
            parent_identity=parent_identity,
            destination_name=destination_name,
            path=path,
        )

    def assert_named(self) -> None:
        if self.staging_fd is not None:
            named = os.stat(
                self.member_name,
                dir_fd=self.staging_fd,
                follow_symlinks=False,
            )
        else:
            named = os.lstat(self.path)
        if (
            not stat.S_ISREG(named.st_mode)
            or (named.st_dev, named.st_ino)
            != (self.identity.st_dev, self.identity.st_ino)
        ):
            raise ArtifactError("Pack temporary path was replaced")

    def commit(self, destination: Path) -> None:
        self.assert_named()
        if self.staging_fd is not None and self.parent_fd is not None:
            os.replace(
                self.member_name,
                self.destination_name,
                src_dir_fd=self.staging_fd,
                dst_dir_fd=self.parent_fd,
            )
            published = os.stat(
                self.destination_name,
                dir_fd=self.parent_fd,
                follow_symlinks=False,
            )
        else:
            os.replace(self.path, destination)
            published = os.lstat(destination)
        if (
            not stat.S_ISREG(published.st_mode)
            or (published.st_dev, published.st_ino)
            != (self.identity.st_dev, self.identity.st_ino)
        ):
            raise ArtifactError("Pack destination was replaced")
        current_parent = self.parent.stat()
        if (current_parent.st_dev, current_parent.st_ino) != (
            self.parent_identity.st_dev,
            self.parent_identity.st_ino,
        ):
            raise ArtifactError("Pack destination parent was replaced")

    def close(self) -> None:
        try:
            os.close(self.fd)
        except OSError:
            pass
        if self.staging_fd is not None:
            try:
                leftover = os.stat(
                    self.member_name,
                    dir_fd=self.staging_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                if (leftover.st_dev, leftover.st_ino) == (
                    self.identity.st_dev,
                    self.identity.st_ino,
                ):
                    os.unlink(self.member_name, dir_fd=self.staging_fd)
            os.close(self.staging_fd)
            if self.parent_fd is not None and self.staging_name is not None:
                try:
                    os.rmdir(self.staging_name, dir_fd=self.parent_fd)
                except OSError:
                    pass
            if self.parent_fd is not None:
                os.close(self.parent_fd)
            return
        try:
            leftover = os.lstat(self.path)
        except FileNotFoundError:
            return
        if (leftover.st_dev, leftover.st_ino) == (
            self.identity.st_dev,
            self.identity.st_ino,
        ):
            os.unlink(self.path)


@dataclass(frozen=True)
class ArtifactEntry:
    path: str
    bytes: int
    sha256: str
    executable: bool

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        candidate = Path(self.path) if isinstance(self.path, str) else Path(".")
        if (
            not isinstance(self.path, str)
            or not self.path
            or _has_control_characters(self.path)
            or "\\" in self.path
            or candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.as_posix() != self.path
            or self.path == "_inventor-artifact.json"
        ):
            raise ArtifactError("artifact entry path is unsafe or reserved")
        if (
            not isinstance(self.bytes, int)
            or isinstance(self.bytes, bool)
            or self.bytes < 0
            or self.bytes > MAX_FILE_BYTES
        ):
            raise ArtifactError("artifact entry byte count is invalid")
        require_sha256(self.sha256, "artifact entry sha256")
        if not isinstance(self.executable, bool):
            raise ArtifactError("artifact entry executable must be boolean")


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: int
    artifact_sha256: str
    entries: Sequence[ArtifactEntry]
    total_bytes: int
    created_at: str

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ArtifactError("artifact manifest schema_version must be 1")
        require_sha256(self.artifact_sha256, "artifact manifest sha256")
        if (
            isinstance(self.entries, (str, bytes))
            or not isinstance(self.entries, Sequence)
            or not self.entries
            or not all(isinstance(entry, ArtifactEntry) for entry in self.entries)
        ):
            raise ArtifactError("artifact manifest requires typed entries")
        for entry in self.entries:
            entry.assert_valid()
        paths = [entry.path for entry in self.entries]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ArtifactError("artifact manifest entries must be unique and sorted")
        total = sum(entry.bytes for entry in self.entries)
        if (
            type(self.total_bytes) is not int
            or self.total_bytes < 0
            or self.total_bytes != total
            or total > MAX_EXPANDED_BYTES
        ):
            raise ArtifactError("artifact manifest total_bytes is inconsistent")
        expected = hashlib.sha256(
            _canonical([asdict(entry) for entry in self.entries])
        ).hexdigest()
        if self.artifact_sha256 != expected:
            raise ArtifactError("artifact manifest identity is inconsistent")
        if self.created_at != "content-addressed":
            require_utc_timestamp(self.created_at, "artifact manifest created_at")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "artifact_sha256": self.artifact_sha256,
            "total_bytes": self.total_bytes,
            "created_at": self.created_at,
            "entries": [asdict(entry) for entry in self.entries],
        }

    def write(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def artifact_manifest_from_mapping(value: Any) -> ArtifactManifest:
    """Strictly reconstruct one canonical content-addressed manifest.

    Native product runs exchange JSON, but deterministic gates operate on
    typed manifests.  Keeping the decoder beside the owning contract avoids
    private copies in orchestration modules.
    """

    expected = {
        "schema_version",
        "artifact_sha256",
        "entries",
        "total_bytes",
        "created_at",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ArtifactError("artifact manifest fields are invalid")
    raw_entries = value["entries"]
    if isinstance(raw_entries, (str, bytes)) or not isinstance(raw_entries, Sequence):
        raise ArtifactError("artifact manifest entries must be an array")
    entries = []
    for raw in raw_entries:
        if not isinstance(raw, Mapping) or set(raw) != {
            "path",
            "bytes",
            "sha256",
            "executable",
        }:
            raise ArtifactError("artifact manifest entry fields are invalid")
        entries.append(
            ArtifactEntry(
                path=raw["path"],
                bytes=raw["bytes"],
                sha256=raw["sha256"],
                executable=raw["executable"],
            )
        )
    manifest = ArtifactManifest(
        schema_version=value["schema_version"],
        artifact_sha256=value["artifact_sha256"],
        entries=tuple(entries),
        total_bytes=value["total_bytes"],
        created_at=value["created_at"],
    )
    if dict(value) != manifest.to_dict():
        raise ArtifactError("artifact manifest is not canonical")
    return manifest


def _excluded(relative: Path, extra_excludes: Set[str]) -> bool:
    parts = relative.parts
    if any(part.lower() in DEFAULT_EXCLUDED_DIRS for part in parts[:-1]):
        return True
    name = relative.name
    lowered = name.lower()
    relative_name = relative.as_posix()
    if name in extra_excludes or relative_name in extra_excludes:
        return True
    if lowered in DEFAULT_EXCLUDED_FILES:
        return True
    if lowered.startswith(DEFAULT_EXCLUDED_PREFIXES) or lowered.endswith(DEFAULT_EXCLUDED_SUFFIXES):
        return True
    return False


def _normalize_extra_excludes(extra_excludes: Iterable[str]) -> Set[str]:
    if isinstance(extra_excludes, (str, bytes)):
        raise ArtifactError("artifact excludes must be an iterable of relative paths")
    normalized = set()
    for value in extra_excludes:
        candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
        if (
            not isinstance(value, str)
            or not value
            or _has_control_characters(value)
            or "\\" in value
            or candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.as_posix() != value
        ):
            raise ArtifactError(
                "artifact exclude must be a safe relative POSIX path"
            )
        normalized.add(value)
    return normalized


def assert_packable_content(relative_path: str, content: bytes) -> None:
    """Apply the final Pack credential policy to one named byte payload.

    Both Pack and the Shop Door call this function. That prevents a
    hand-built, manifest-valid zip from bypassing the source-tree exclusions.
    """
    if (
        not isinstance(relative_path, str)
        or _has_control_characters(relative_path)
        or not isinstance(content, bytes)
    ):
        raise ArtifactError("Packable content requires a path and bytes")
    _assert_path_has_no_secret(relative_path)
    relative = Path(*relative_path.split("/"))
    if _excluded(relative, set()):
        raise ArtifactError("artifact entry is excluded from publication: %s" % relative_path)
    for rule, pattern in SECRET_PATTERNS.items():
        if pattern.search(content):
            raise ArtifactError(
                "artifact file %s matches secret rule %s" % (relative_path, rule)
            )


def _source_files(root: Path, extra_excludes: Iterable[str] = ()) -> List[Tuple[Path, Path]]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise ArtifactError("artifact root is not a directory: %s" % root)
    excluded = _normalize_extra_excludes(extra_excludes)
    result = []
    for directory, dirnames, filenames in os.walk(str(root), followlinks=False):
        base = Path(directory)
        kept_dirs = []
        for dirname in sorted(dirnames):
            absolute = base / dirname
            relative = absolute.relative_to(root)
            if dirname.lower() in DEFAULT_EXCLUDED_DIRS or _excluded(relative, excluded):
                continue
            _assert_path_has_no_secret(relative.as_posix())
            if absolute.is_symlink():
                raise ArtifactError("artifact contains symlink: %s" % relative.as_posix())
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in sorted(filenames):
            absolute = base / filename
            relative = absolute.relative_to(root)
            if _excluded(relative, excluded):
                continue
            _assert_path_has_no_secret(relative.as_posix())
            if (
                "\\" in relative.as_posix()
                or _has_control_characters(relative.as_posix())
                or ".." in relative.parts
            ):
                raise ArtifactError("artifact contains an unsafe path: %s" % relative.as_posix())
            if absolute.is_symlink():
                raise ArtifactError("artifact contains symlink: %s" % relative.as_posix())
            if not absolute.is_file():
                raise ArtifactError("artifact entry is not a regular file: %s" % relative)
            result.append((relative, absolute))
    result.sort(key=lambda pair: pair[0].as_posix())
    if not result:
        raise ArtifactError("artifact has no files eligible for a Pack")
    if len(result) > MAX_ENTRIES:
        raise ArtifactError("artifact has %d files; limit is %d" % (len(result), MAX_ENTRIES))
    return result


def build_artifact_manifest(
    root: Path,
    extra_excludes: Iterable[str] = (),
    created_at: Optional[str] = None,
    maximum_file_bytes: int = MAX_FILE_BYTES,
    maximum_total_bytes: int = MAX_EXPANDED_BYTES,
) -> ArtifactManifest:
    root = Path(root).resolve()
    for value, label in (
        (maximum_file_bytes, "artifact file limit"),
        (maximum_total_bytes, "artifact expanded-size limit"),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ArtifactError("%s must be a positive integer" % label)
    entries = []
    for relative, absolute in _source_files(root, extra_excludes):
        del absolute
        digest, after = _hash_open_file(root, relative)
        if after.st_size > maximum_file_bytes:
            raise ArtifactError(
                "artifact file %s is %d bytes; limit is %d"
                % (relative.as_posix(), after.st_size, maximum_file_bytes)
            )
        entries.append(
            ArtifactEntry(
                path=relative.as_posix(),
                bytes=after.st_size,
                sha256=digest,
                executable=bool(after.st_mode & stat.S_IXUSR),
            )
        )
    total_bytes = sum(entry.bytes for entry in entries)
    if total_bytes > maximum_total_bytes:
        raise ArtifactError(
            "artifact expands to %d bytes; limit is %d"
            % (total_bytes, maximum_total_bytes)
        )
    identity = [asdict(entry) for entry in entries]
    artifact_sha = hashlib.sha256(_canonical(identity)).hexdigest()
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=artifact_sha,
        entries=tuple(entries),
        total_bytes=total_bytes,
        created_at=created_at or utc_now(),
    )


def build_pack(
    root: Path,
    destination: Path,
    extra_excludes: Iterable[str] = (),
    maximum_bytes: int = MAX_PACK_BYTES,
) -> Dict[str, Any]:
    """Write a reproducible zip and return its immutable identity.

    Zip timestamps, permissions, ordering, and compression settings are
    fixed, so identical input bytes produce identical Pack bytes on every
    inventor machine.
    """

    maximum_bytes = _validate_pack_limit(maximum_bytes)
    root = Path(root).resolve()
    extra_excludes = _normalize_extra_excludes(extra_excludes)
    requested_destination = Path(destination)
    if requested_destination.name in ("", ".", ".."):
        raise ArtifactError("Pack destination must name one file")
    if requested_destination.is_symlink():
        raise ArtifactError("Pack destination must not be a symlink")
    parent_missing = not requested_destination.parent.exists()
    requested_destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if parent_missing:
        os.chmod(str(requested_destination.parent), 0o700)
    # Resolve the parent, not the final component.  os.replace then replaces a
    # raced destination symlink itself instead of following it to another file.
    destination = requested_destination.parent.resolve() / requested_destination.name
    try:
        destination.relative_to(root)
    except ValueError:
        pass
    else:
        raise ArtifactError("Pack destination must be outside the artifact root")
    files = _source_files(root, extra_excludes)
    manifest = build_artifact_manifest(root, extra_excludes, created_at="content-addressed")
    manifest_by_path = {entry.path: entry for entry in manifest.entries}
    if [relative.as_posix() for relative, _ in files] != [entry.path for entry in manifest.entries]:
        raise ArtifactError("artifact file inventory changed while packaging")
    # Workshop Packs use ZIP_STORED with no comments or extra fields, so the
    # final byte count is knowable before a temporary file is written.  Fail
    # early with an actionable inventory instead of spending time copying a
    # tree only to report one opaque number at the end.
    manifest_content = _canonical(manifest.to_dict()) + b"\n"
    planned_members = [
        (entry.path, entry.bytes) for entry in manifest.entries
    ] + [("_inventor-artifact.json", len(manifest_content))]
    planned_bytes = 22 + sum(
        size + 76 + 2 * len(path.encode("utf-8"))
        for path, size in planned_members
    )
    if planned_bytes > maximum_bytes:
        largest = sorted(
            manifest.entries,
            key=lambda entry: (-entry.bytes, entry.path),
        )[:5]
        inventory = ", ".join(
            "%s (%d bytes)" % (entry.path, entry.bytes)
            for entry in largest
        )
        raise ArtifactError(
            "Pack would be %d bytes; configured limit is %d; largest eligible "
            "files: %s. Stage product-only files or use extra_excludes."
            % (planned_bytes, maximum_bytes, inventory or "none")
        )
    staging = _PackStaging.create(destination.parent, destination.name)
    fd = staging.fd
    opened_identity = staging.identity
    size = None
    pack_sha = None
    try:
        # Stored members avoid zlib-version-dependent DEFLATE byte streams.
        # The backend expands the archive anyway; exact cross-machine Pack
        # identity is more valuable here than local transfer compression.
        with os.fdopen(fd, "w+b", closefd=False) as handle:
            with zipfile.ZipFile(
                handle, "w", compression=zipfile.ZIP_STORED
            ) as archive:
                for relative, absolute in files:
                    del absolute
                    content, opened = _read_open_file(root, relative)
                    expected = manifest_by_path[relative.as_posix()]
                    if (
                        not stat.S_ISREG(opened.st_mode)
                        or len(content) != expected.bytes
                        or hashlib.sha256(content).hexdigest() != expected.sha256
                        or bool(opened.st_mode & stat.S_IXUSR) != expected.executable
                    ):
                        raise ArtifactError(
                            "artifact changed while packaging: %s"
                            % relative.as_posix()
                        )
                    assert_packable_content(relative.as_posix(), content)
                    info = zipfile.ZipInfo(
                        relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0)
                    )
                    info.compress_type = zipfile.ZIP_STORED
                    info.create_system = 3
                    executable = expected.executable
                    info.external_attr = (
                        (0o755 if executable else 0o644) & 0xFFFF
                    ) << 16
                    archive.writestr(
                        info, content, compress_type=zipfile.ZIP_STORED
                    )
                info = zipfile.ZipInfo(
                    "_inventor-artifact.json",
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o644 & 0xFFFF) << 16
                archive.writestr(info, manifest_content)
            handle.flush()
            os.fsync(fd)
        completed = os.fstat(fd)
        if (
            not stat.S_ISREG(completed.st_mode)
            or (completed.st_dev, completed.st_ino)
            != (opened_identity.st_dev, opened_identity.st_ino)
        ):
            raise ArtifactError("Pack temporary file identity changed")
        size = completed.st_size
        if size > maximum_bytes:
            raise ArtifactError(
                "Pack is %d bytes; configured limit is %d" % (size, maximum_bytes)
            )
        digest = hashlib.sha256()
        os.lseek(fd, 0, os.SEEK_SET)
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        pack_sha = digest.hexdigest()
        staging.commit(destination)
    finally:
        staging.close()
    return {
        "path": str(destination),
        "bytes": size,
        "entries": len(files) + 1,
        "pack_sha256": pack_sha,
        "artifact_sha256": manifest.artifact_sha256,
    }
