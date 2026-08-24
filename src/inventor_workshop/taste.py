"""Content-bound creative constitutions for autonomous inventors."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .errors import ManifestError
from .models import require_sha256


MAX_TASTE_BYTES = 256 * 1024


def _read_taste_bytes(path: Path) -> bytes:
    """Read one regular file without following a raced final symlink."""

    try:
        expected = path.lstat()
    except FileNotFoundError:
        raise ManifestError("missing inventor Taste: %s" % path)
    except OSError as exc:
        raise ManifestError("cannot inspect %s: %s" % (path, exc)) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ManifestError("inventor TASTE.md must be a regular file: %s" % path)

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ManifestError("cannot safely open %s: %s" % (path, exc)) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (expected.st_dev, expected.st_ino):
            raise ManifestError("inventor TASTE.md changed while opening: %s" % path)
        chunks = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, MAX_TASTE_BYTES + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > MAX_TASTE_BYTES:
                raise ManifestError(
                    "inventor TASTE.md exceeds %d bytes: %s" % (MAX_TASTE_BYTES, path)
                )
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ManifestError("inventor TASTE.md changed while reading: %s" % path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


@dataclass(frozen=True)
class Taste:
    """The exact UTF-8 bytes of an inventor root's ``TASTE.md``.

    The digest is over the source bytes, not normalized Markdown. This makes a
    concept request reproducibly attributable to the creative constitution that
    the agent actually saw.
    """

    schema_version: int
    path: Path
    content: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ManifestError("Taste schema_version must be 1")
        if not self.path.is_absolute() or self.path.name != "TASTE.md":
            raise ManifestError("Taste path must be an absolute root TASTE.md")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ManifestError("Taste content must be non-empty UTF-8")
        try:
            encoded = self.content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ManifestError("Taste content must be valid UTF-8") from exc
        if (
            type(self.byte_count) is not int
            or self.byte_count <= 0
            or self.byte_count > MAX_TASTE_BYTES
            or len(encoded) != self.byte_count
        ):
            raise ManifestError("Taste byte count is inconsistent")
        require_sha256(self.sha256, "Taste sha256")
        if hashlib.sha256(encoded).hexdigest() != self.sha256:
            raise ManifestError("Taste identity is inconsistent")

    def to_binding(self) -> Dict[str, Any]:
        """Return the complete, JSON-safe binding sent to a creative agent."""

        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "path": "TASTE.md",
            "sha256": self.sha256,
            "bytes": self.byte_count,
            "content": self.content,
        }

    def assert_current(self) -> None:
        current = load_taste(self.path.parent)
        if current.sha256 != self.sha256 or current.content != self.content:
            raise ManifestError("inventor TASTE.md changed during Make: %s" % self.path)


def load_taste(inventor_root: Path) -> Taste:
    """Load the immediate ``TASTE.md`` under one real inventor directory."""

    requested_root = Path(inventor_root)
    if requested_root.is_symlink():
        raise ManifestError("inventor root must not be a symlink: %s" % requested_root)
    try:
        root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("cannot resolve inventor root %s: %s" % (requested_root, exc)) from exc
    if not root.is_dir():
        raise ManifestError("inventor root must be a directory: %s" % root)
    path = root / "TASTE.md"
    source = _read_taste_bytes(path)
    try:
        content = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("inventor TASTE.md must be UTF-8: %s" % path) from exc
    if not content.strip():
        raise ManifestError("inventor TASTE.md must be non-empty: %s" % path)
    return Taste(
        schema_version=1,
        path=path,
        content=content,
        sha256=hashlib.sha256(source).hexdigest(),
        byte_count=len(source),
    )


# Compatibility spellings used before Workshop 0.3.
TasteProfile = Taste
load_taste_profile = load_taste
