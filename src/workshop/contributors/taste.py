"""Skill-like creative constitutions with cheap progressive disclosure."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from workshop.errors import ManifestError
from workshop._validation import require_sha256


MAX_TASTE_BYTES = 256 * 1024
MAX_TASTE_HEADER_BYTES = 8 * 1024
MAX_TASTE_NAME_CHARS = 200
MAX_TASTE_DESCRIPTION_CHARS = 500


def _taste_path(inventor_root: Path) -> Path:
    requested_root = Path(inventor_root)
    if requested_root.is_symlink():
        raise ManifestError("inventor root must not be a symlink: %s" % requested_root)
    try:
        root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("cannot resolve inventor root %s: %s" % (requested_root, exc)) from exc
    if not root.is_dir():
        raise ManifestError("inventor root must be a directory: %s" % root)
    return root / "TASTE.md"


def _open_taste(path: Path) -> tuple[int, os.stat_result]:
    try:
        expected = path.lstat()
    except FileNotFoundError:
        raise ManifestError("missing inventor Taste: %s" % path)
    except OSError as exc:
        raise ManifestError("cannot inspect %s: %s" % (path, exc)) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ManifestError("inventor TASTE.md must be a regular file: %s" % path)
    if expected.st_size <= 0 or expected.st_size > MAX_TASTE_BYTES:
        raise ManifestError(
            "inventor TASTE.md must contain 1 to %d bytes: %s"
            % (MAX_TASTE_BYTES, path)
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ManifestError("cannot safely open %s: %s" % (path, exc)) from exc
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        os.close(descriptor)
        raise ManifestError("inventor TASTE.md changed while opening: %s" % path)
    return descriptor, opened


def _assert_unchanged(descriptor: int, opened: os.stat_result, path: Path) -> None:
    after = os.fstat(descriptor)
    if (
        after.st_size != opened.st_size
        or after.st_mtime_ns != opened.st_mtime_ns
        or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        raise ManifestError("inventor TASTE.md changed while reading: %s" % path)


def _header_prefix(source: bytes, path: Path) -> bytes:
    if source.startswith(b"---\n"):
        marker = b"\n---\n"
        start = 4
    elif source.startswith(b"---\r\n"):
        marker = b"\r\n---\r\n"
        start = 5
    else:
        raise ManifestError("inventor TASTE.md must begin with YAML frontmatter: %s" % path)
    closing = source.find(marker, start)
    if closing < 0:
        raise ManifestError("inventor TASTE.md has no closing frontmatter delimiter: %s" % path)
    end = closing + len(marker)
    if end > MAX_TASTE_HEADER_BYTES:
        raise ManifestError(
            "inventor TASTE.md frontmatter exceeds %d bytes: %s"
            % (MAX_TASTE_HEADER_BYTES, path)
        )
    return source[:end]


def _read_taste_header_bytes(path: Path) -> bytes:
    """Return only frontmatter while using bounded buffered filesystem reads."""

    descriptor, opened = _open_taste(path)
    try:
        source = bytearray()
        while len(source) <= MAX_TASTE_HEADER_BYTES:
            chunk = os.read(
                descriptor,
                min(1024, MAX_TASTE_HEADER_BYTES + 1 - len(source)),
            )
            if not chunk:
                break
            source.extend(chunk)
            if source.startswith(b"---\n"):
                marker = b"\n---\n"
                closing = source.find(marker, 4)
            elif source.startswith(b"---\r\n"):
                marker = b"\r\n---\r\n"
                closing = source.find(marker, 5)
            elif len(source) >= 5:
                raise ManifestError(
                    "inventor TASTE.md must begin with YAML frontmatter: %s" % path
                )
            else:
                closing = -1
                marker = b""
            if closing >= 0:
                _assert_unchanged(descriptor, opened, path)
                return bytes(source[: closing + len(marker)])
        if len(source) > MAX_TASTE_HEADER_BYTES:
            raise ManifestError(
                "inventor TASTE.md frontmatter exceeds %d bytes: %s"
                % (MAX_TASTE_HEADER_BYTES, path)
            )
        # Reuse the precise syntax error for a missing opening or closing marker.
        _header_prefix(bytes(source), path)
        raise ManifestError("inventor TASTE.md frontmatter is incomplete: %s" % path)
    finally:
        os.close(descriptor)


def _read_taste_bytes(path: Path) -> bytes:
    """Read the complete bounded constitution for a shortlisted inventor."""

    descriptor, opened = _open_taste(path)
    try:
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
        _assert_unchanged(descriptor, opened, path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _yaml_scalar(raw: str, label: str, maximum: int, path: Path) -> str:
    raw = raw.strip()
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except ValueError as exc:
            raise ManifestError("%s has invalid quoted %s" % (path, label)) from exc
    else:
        if not raw or raw[0] in "'|>&*!{}[]":
            raise ManifestError("%s %s must be plain text or a JSON-quoted string" % (path, label))
        value = raw
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ManifestError("%s %s must be 1 to %d control-free characters" % (path, label, maximum))
    return value.strip()


def _parse_taste_header(source: bytes, path: Path) -> "TasteHeader":
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("inventor TASTE.md frontmatter must be UTF-8: %s" % path) from exc
    lines = text.splitlines()
    if len(lines) != 4 or lines[0] != "---" or lines[-1] != "---":
        raise ManifestError(
            "%s frontmatter must contain exactly name and description" % path
        )
    parsed: Dict[str, str] = {}
    for line in lines[1:3]:
        if ":" not in line:
            raise ManifestError("%s frontmatter fields must use key: value" % path)
        key, raw = line.split(":", 1)
        if key not in ("name", "description") or key in parsed:
            raise ManifestError(
                "%s frontmatter allows exactly one name and one description" % path
            )
        maximum = MAX_TASTE_NAME_CHARS if key == "name" else MAX_TASTE_DESCRIPTION_CHARS
        parsed[key] = _yaml_scalar(raw, key, maximum, path)
    if tuple(parsed) != ("name", "description"):
        raise ManifestError("%s frontmatter order must be name then description" % path)
    return TasteHeader(
        schema_version=1,
        path=path,
        name=parsed["name"],
        description=parsed["description"],
        sha256=hashlib.sha256(source).hexdigest(),
        byte_count=len(source),
    )


@dataclass(frozen=True)
class TasteHeader:
    """Cheap discovery metadata from the exact YAML frontmatter bytes."""

    schema_version: int
    path: Path
    name: str
    description: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ManifestError("TasteHeader schema_version must be 1")
        if not self.path.is_absolute() or self.path.name != "TASTE.md":
            raise ManifestError("TasteHeader path must be an absolute root TASTE.md")
        _yaml_scalar(self.name, "name", MAX_TASTE_NAME_CHARS, self.path)
        _yaml_scalar(
            self.description, "description", MAX_TASTE_DESCRIPTION_CHARS, self.path
        )
        require_sha256(self.sha256, "TasteHeader sha256")
        if type(self.byte_count) is not int or not 1 <= self.byte_count <= MAX_TASTE_HEADER_BYTES:
            raise ManifestError("TasteHeader byte count is inconsistent")

    def to_binding(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "path": "TASTE.md",
            "name": self.name,
            "description": self.description,
            "sha256": self.sha256,
            "bytes": self.byte_count,
        }

    def assert_current(self) -> None:
        current = load_taste_header(self.path.parent)
        if current.to_binding() != self.to_binding():
            raise ManifestError("inventor TASTE.md header changed during routing: %s" % self.path)


@dataclass(frozen=True)
class Taste:
    """The complete exact UTF-8 constitution of a shortlisted inventor."""

    schema_version: int
    path: Path
    content: str
    sha256: str
    byte_count: int
    header: TasteHeader

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        self.assert_valid()

    @property
    def name(self) -> str:
        return self.header.name

    @property
    def description(self) -> str:
        return self.header.description

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ManifestError("Taste schema_version must be 1")
        if not self.path.is_absolute() or self.path.name != "TASTE.md":
            raise ManifestError("Taste path must be an absolute root TASTE.md")
        if not isinstance(self.header, TasteHeader) or self.header.path != self.path:
            raise ManifestError("Taste requires its exact parsed frontmatter")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ManifestError("Taste content must be non-empty UTF-8")
        try:
            encoded = self.content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ManifestError("Taste content must be valid UTF-8") from exc
        header_source = _header_prefix(encoded, self.path)
        if hashlib.sha256(header_source).hexdigest() != self.header.sha256:
            raise ManifestError("Taste header identity is inconsistent")
        if not encoded[len(header_source) :].strip():
            raise ManifestError("Taste must contain a Markdown constitution after frontmatter")
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
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "path": "TASTE.md",
            "sha256": self.sha256,
            "bytes": self.byte_count,
            "header": self.header.to_binding(),
            "content": self.content,
        }

    def assert_current(self) -> None:
        current = load_taste(self.path.parent)
        if current.sha256 != self.sha256 or current.content != self.content:
            raise ManifestError("inventor TASTE.md changed during Make: %s" % self.path)


def load_taste_header(inventor_root: Path) -> TasteHeader:
    """Load only strict discovery frontmatter, never the constitution body."""

    path = _taste_path(inventor_root)
    return _parse_taste_header(_read_taste_header_bytes(path), path)


def load_taste(inventor_root: Path) -> Taste:
    """Load the complete strict ``TASTE.md`` for a shortlisted inventor."""

    path = _taste_path(inventor_root)
    source = _read_taste_bytes(path)
    try:
        content = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("inventor TASTE.md must be UTF-8: %s" % path) from exc
    header_source = _header_prefix(source, path)
    header = _parse_taste_header(header_source, path)
    return Taste(
        schema_version=1,
        path=path,
        content=content,
        sha256=hashlib.sha256(source).hexdigest(),
        byte_count=len(source),
        header=header,
    )


def parse_taste_bytes(source: bytes, *, path: Path) -> Taste:
    """Parse exact embedded Taste bytes without requiring a duplicate file.

    Product projects bind Taste inside ``.codex/agents/<inventor>.toml``.  The
    trusted host uses this parser after validating that custom-agent file,
    rather than materializing a second Inventor identity tree.
    """

    selected_path = Path(path)
    if (
        not selected_path.is_absolute()
        or selected_path.name != "TASTE.md"
        or not isinstance(source, bytes)
        or not 1 <= len(source) <= MAX_TASTE_BYTES
    ):
        raise ManifestError("embedded Inventor Taste path or bytes are invalid")
    try:
        content = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("embedded Inventor Taste must be UTF-8") from exc
    header_source = _header_prefix(source, selected_path)
    header = _parse_taste_header(header_source, selected_path)
    return Taste(
        schema_version=1,
        path=selected_path,
        content=content,
        sha256=hashlib.sha256(source).hexdigest(),
        byte_count=len(source),
        header=header,
    )


__all__ = [
    "MAX_TASTE_BYTES",
    "MAX_TASTE_DESCRIPTION_CHARS",
    "MAX_TASTE_HEADER_BYTES",
    "MAX_TASTE_NAME_CHARS",
    "Taste",
    "TasteHeader",
    "load_taste",
    "parse_taste_bytes",
    "load_taste_header",
]
