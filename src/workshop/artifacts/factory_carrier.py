"""Explicit compressed Factory carrier for Make's mixed public projection.

Canonical Packs remain ZIP_STORED. This separate profile preserves their
inventory identity and bounds, with fixed DEFLATE settings when first built.
Compressed bytes are not promised to match across zlib versions: the host must
persist the first carrier and bind/reuse its exact pack hash before an effect.
"""

from __future__ import annotations

import binascii
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import zipfile
import zlib

from workshop.artifacts.core import (
    MAX_ENTRIES, MAX_EXPANDED_BYTES, MAX_FILE_BYTES, MAX_PACK_BYTES,
    _PackStaging, _canonical, _open_regular_no_follow, _source_files,
    artifact_manifest_from_mapping, assert_packable_content, build_artifact_manifest,
)
from workshop.artifacts.pack import _read_pack_bytes, _safe_pack_path
from workshop.errors import ContractError


MIXED_CARRIER_FORMAT = "factory-mixed-deflate-v1"
_MANIFEST = "_inventor-artifact.json"
_DATE = (1980, 1, 1, 0, 0, 0)
_CHUNK = 1024 * 1024


def _fail(message: str):
    raise ContractError("Mixed Factory carrier " + message)


def _name_bytes(name: str) -> tuple[bytes, int]:
    _safe_pack_path(name)
    try:
        return name.encode("ascii"), 0
    except UnicodeEncodeError:
        return name.encode("utf-8"), 0x800


def _info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o755 if executable else 0o644) << 16
    return info


def _directory_bounds(content: bytes) -> tuple[int, int]:
    """Bound the actual central record count before ZipFile allocates its index."""
    if len(content) < 22:
        _fail("is truncated")
    end = struct.unpack_from("<4s4H2IH", content, len(content) - 22)
    signature, disk, start_disk, disk_count, count, central_size, central_start, comment = end
    if (signature != b"PK\x05\x06" or disk or start_disk or comment or disk_count != count
            or not 2 <= count <= MAX_ENTRIES + 1
            or central_start + central_size != len(content) - 22):
        _fail("has noncanonical end records, trailing bytes or member count")
    cursor = central_start
    for _ in range(count):
        if cursor + 46 > len(content) - 22 or content[cursor:cursor + 4] != b"PK\x01\x02":
            _fail("has a truncated or inconsistent central directory")
        name_size, extra_size, comment_size = struct.unpack_from("<3H", content, cursor + 28)
        cursor += 46 + name_size + extra_size + comment_size
    if cursor != len(content) - 22:
        _fail("actual central member count differs from its bounded end record")
    return count, central_start


def _physical_members(content: bytes, archive: zipfile.ZipFile,
                      count: int, central_start: int) -> list[zipfile.ZipInfo]:
    """Require contiguous canonical headers and no hidden ZIP/container bytes."""
    infos = archive.infolist()
    if archive.comment or len(infos) != count:
        _fail("has inconsistent inventory or comments")
    names = [info.filename for info in infos]
    if len(set(names)) != len(names) or names.count(_MANIFEST) != 1:
        _fail("has duplicate members or lacks its unique inventory")
    if any(info.file_size > MAX_FILE_BYTES for info in infos):
        _fail("contains an oversized expanded member")
    if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
        _fail("exceeds the expanded-size limit")
    local_cursor = 0
    central_cursor = central_start
    name_set = set(names)
    for info in infos:
        name, flags = _name_bytes(info.filename)
        if any(parent.as_posix() in name_set for parent in Path(info.filename).parents
               if parent.as_posix() != "."):
            _fail("contains conflicting file and directory paths")
        if (info.is_dir() or info.compress_type != zipfile.ZIP_DEFLATED
                or info.date_time != _DATE or info.create_system != 3
                or info.create_version != 20 or info.extract_version != 20
                or info.reserved or info.flag_bits != flags or info.volume
                or info.internal_attr or info.extra or info.comment
                or info.external_attr not in (0o644 << 16, 0o755 << 16)
                or info.header_offset != local_cursor):
            _fail("contains noncanonical member metadata or overlapping records")
        local = struct.pack("<4s5H3I2H", b"PK\x03\x04", 20, flags, 8, 0, 33,
                            info.CRC, info.compress_size, info.file_size, len(name), 0) + name
        if content[local_cursor:local_cursor + len(local)] != local:
            _fail("local header disagrees with its central directory")
        local_cursor += len(local) + info.compress_size
        if local_cursor > central_start:
            _fail("member data overlaps its central directory")
        central = struct.pack("<4s6H3I5H2I", b"PK\x01\x02", (3 << 8) | 20, 20,
                              flags, 8, 0, 33, info.CRC, info.compress_size, info.file_size,
                              len(name), 0, 0, 0, 0, info.external_attr, info.header_offset) + name
        if content[central_cursor:central_cursor + len(central)] != central:
            _fail("central directory is not canonical")
        central_cursor += len(central)
    if local_cursor != central_start or central_cursor != len(content) - 22:
        _fail("contains gaps or unbound archive bytes")
    return infos


def _member_bytes(content: bytes, info: zipfile.ZipInfo) -> bytes:
    """Bound expansion and reject even unused bytes inside a DEFLATE member."""
    name, _ = _name_bytes(info.filename)
    start = info.header_offset + 30 + len(name)
    compressed = memoryview(content)[start:start + info.compress_size]
    inflater = zlib.decompressobj(-15)
    chunks = []
    size = 0
    for offset in range(0, len(compressed), 64 * 1024):
        pending = compressed[offset:offset + 64 * 1024]
        while pending:
            block = inflater.decompress(pending, min(_CHUNK, info.file_size - size + 1))
            size += len(block)
            if size > info.file_size:
                _fail("member expands beyond its declared size")
            if block:
                chunks.append(block)
            if inflater.unused_data:
                _fail("contains bytes after its member DEFLATE stream")
            remainder = inflater.unconsumed_tail
            if not block and remainder == pending:
                _fail("member DEFLATE stream made no progress")
            pending = remainder
    if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail or size != info.file_size:
        _fail("member DEFLATE stream is truncated or has an invalid size")
    member = b"".join(chunks)
    if binascii.crc32(member) & 0xFFFFFFFF != info.CRC:
        _fail("member CRC differs")
    return member


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("inventory contains a duplicate JSON key")
        result[key] = value
    return result


def validate_mixed_carrier(content: bytes) -> tuple[bytes, str, str]:
    """Validate exact transport bytes and canonical expanded inventory, not zlib output."""
    if type(content) is not bytes or not content:
        _fail("must be non-empty immutable bytes")
    if len(content) > MAX_PACK_BYTES:
        _fail("exceeds the 50 MiB compressed limit")
    try:
        count, central_start = _directory_bounds(content)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = _physical_members(content, archive, count, central_start)
        by_name = {info.filename: info for info in infos}
        manifest_content = _member_bytes(content, by_name[_MANIFEST])
        raw = json.loads(manifest_content.decode("utf-8"), object_pairs_hook=_strict_pairs,
                         parse_constant=lambda value: _fail("inventory contains non-finite JSON"))
        manifest = artifact_manifest_from_mapping(raw)
        if (manifest.created_at != "content-addressed"
                or manifest_content != _canonical(manifest.to_dict()) + b"\n"
                or len(manifest.entries) > MAX_ENTRIES):
            _fail("inventory is not canonical")
        expected_names = [entry.path for entry in manifest.entries] + [_MANIFEST]
        if [info.filename for info in infos] != expected_names:
            _fail("inventory differs from member order or includes unbound members")
        if by_name[_MANIFEST].external_attr != 0o644 << 16:
            _fail("inventory permissions differ")
        for entry in manifest.entries:
            info = by_name[entry.path]
            if (info.file_size != entry.bytes
                    or info.external_attr != (0o755 if entry.executable else 0o644) << 16):
                _fail("member size or permissions differ from inventory")
            member = _member_bytes(content, info)
            assert_packable_content(entry.path, member)
            if hashlib.sha256(member).hexdigest() != entry.sha256:
                _fail("member hash differs from inventory")
            del member
        return content, hashlib.sha256(content).hexdigest(), manifest.artifact_sha256
    except (OSError, UnicodeError, ValueError, RecursionError, struct.error,
            zipfile.BadZipFile, zlib.error) as exc:
        raise ContractError("Mixed Factory carrier is malformed") from exc


def load_mixed_carrier(path: Path) -> tuple[bytes, str, str]:
    """Use the existing bounded no-follow reader for the persisted exact carrier."""
    return validate_mixed_carrier(_read_pack_bytes(Path(path)))


class _BoundedWriter:
    def __init__(self, handle):
        self.handle = handle

    def __getattr__(self, name):
        return getattr(self.handle, name)

    def write(self, content):
        if self.handle.tell() + len(content) > MAX_PACK_BYTES:
            _fail("exceeds the 50 MiB compressed limit")
        return self.handle.write(content)


def _source_member(root, relative, expected):
    descriptor, opened = _open_regular_no_follow(root, relative)
    try:
        if opened.st_size != expected.bytes or opened.st_size > MAX_FILE_BYTES:
            _fail("source size changed while packaging")
        chunks = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(_CHUNK, expected.bytes - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > expected.bytes:
                _fail("source grew while packaging")
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (size != expected.bytes or opened.st_size != after.st_size
                or opened.st_mtime_ns != after.st_mtime_ns
                or bool(after.st_mode & stat.S_IXUSR) != expected.executable):
            _fail("source changed while packaging")
        member = b"".join(chunks)
        if hashlib.sha256(member).hexdigest() != expected.sha256:
            _fail("source hash changed while packaging")
        return member
    finally:
        os.close(descriptor)


def build_mixed_carrier(root: Path, destination: Path) -> dict:
    """Build one private bounded carrier; integration owns durable reuse before intent."""
    root = Path(root).resolve(strict=True)
    destination = Path(destination)
    if destination.name in ("", ".", "..") or destination.is_symlink():
        _fail("destination is invalid or a symlink")
    missing_parent = not destination.parent.exists()
    destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if missing_parent:
        destination.parent.chmod(0o700)
    destination = destination.parent.resolve() / destination.name
    if destination.is_relative_to(root):
        _fail("destination must be outside the source tree")
    files = _source_files(root)
    manifest = build_artifact_manifest(root, created_at="content-addressed")
    if [relative.as_posix() for relative, _ in files] != [entry.path for entry in manifest.entries]:
        _fail("source inventory changed while packaging")
    staging = _PackStaging.create(destination.parent, destination.name)
    try:
        with os.fdopen(staging.fd, "w+b", closefd=False) as handle:
            with zipfile.ZipFile(_BoundedWriter(handle), "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9, allowZip64=False) as archive:
                for (relative, _), expected in zip(files, manifest.entries):
                    member = _source_member(root, relative, expected)
                    assert_packable_content(relative.as_posix(), member)
                    archive.writestr(_info(expected.path, expected.executable), member, compresslevel=9)
                    del member
                archive.writestr(_info(_MANIFEST), _canonical(manifest.to_dict()) + b"\n", compresslevel=9)
            handle.flush()
            os.fsync(staging.fd)
            completed = os.fstat(staging.fd)
            if (not stat.S_ISREG(completed.st_mode) or completed.st_size > MAX_PACK_BYTES
                    or (completed.st_dev, completed.st_ino) != (staging.identity.st_dev, staging.identity.st_ino)):
                _fail("temporary file changed or exceeds its limit")
            handle.seek(0)
            content, pack_sha, artifact_sha = validate_mixed_carrier(handle.read(MAX_PACK_BYTES + 1))
        if artifact_sha != manifest.artifact_sha256:
            _fail("inventory changed after construction")
        staging.commit(destination)
    finally:
        staging.close()
    return {"path": str(destination), "bytes": len(content), "entries": len(files) + 1,
            "pack_sha256": pack_sha, "artifact_sha256": artifact_sha}
