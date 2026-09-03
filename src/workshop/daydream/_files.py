"""Private bounded, symlink-free file helpers for Daydream state."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from workshop.daydream.contracts import DaydreamError


_OPEN_FLAGS = getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)


def _assert_same_regular_file(
    descriptor: int, expected: os.stat_result, path: Path, label: str
) -> os.stat_result:
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        raise DaydreamError("%s changed while opening: %s" % (label, path))
    return opened


def read_regular_bytes(path: Path, *, maximum: int, label: str) -> bytes:
    """Read one regular file of at most ``maximum`` bytes without following links.

    A missing file raises ``FileNotFoundError`` so callers can decide whether
    absence is an error; every other problem raises ``DaydreamError``.
    """

    try:
        expected = path.lstat()
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise DaydreamError("cannot inspect %s: %s" % (label, path)) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise DaydreamError("%s must be a regular file: %s" % (label, path))
    if expected.st_size > maximum:
        raise DaydreamError("%s exceeds %d bytes: %s" % (label, maximum, path))
    try:
        descriptor = os.open(str(path), os.O_RDONLY | _OPEN_FLAGS)
    except OSError as exc:
        raise DaydreamError("cannot open %s: %s" % (label, path)) from exc
    try:
        _assert_same_regular_file(descriptor, expected, path, label)
        chunks = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise DaydreamError("%s exceeds %d bytes: %s" % (label, maximum, path))
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        view = view[written:]


def write_private_bytes(path: Path, data: bytes, *, label: str) -> None:
    """Create one new owner-only file exclusively; an existing path fails."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _OPEN_FLAGS
    try:
        descriptor = os.open(str(path), flags, 0o600)
    except FileExistsError as exc:
        raise DaydreamError("%s already exists: %s" % (label, path)) from exc
    except OSError as exc:
        raise DaydreamError("cannot create %s: %s" % (label, path)) from exc
    try:
        os.fchmod(descriptor, 0o600)
        _write_all(descriptor, data)
    finally:
        os.close(descriptor)


def append_private_line(path: Path, line: bytes, *, label: str) -> None:
    """Append one record to an owner-only regular file, creating it if absent."""

    try:
        before = path.lstat()
    except FileNotFoundError:
        before = None
    except OSError as exc:
        raise DaydreamError("cannot inspect %s: %s" % (label, path)) from exc
    if before is not None:
        if path.is_symlink() or not stat.S_ISREG(before.st_mode):
            raise DaydreamError("%s must be a regular file: %s" % (label, path))
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise DaydreamError("%s permissions must be 0600: %s" % (label, path))
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | _OPEN_FLAGS
    try:
        descriptor = os.open(str(path), flags, 0o600)
    except OSError as exc:
        raise DaydreamError("cannot open %s: %s" % (label, path)) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise DaydreamError("%s must be a regular file: %s" % (label, path))
        if before is None:
            os.fchmod(descriptor, 0o600)
        elif (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise DaydreamError("%s changed while opening: %s" % (label, path))
        _write_all(descriptor, line)
    finally:
        os.close(descriptor)


__all__ = ["append_private_line", "read_regular_bytes", "write_private_bytes"]
