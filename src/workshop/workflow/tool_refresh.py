"""Bounded native handoff for an already completed, host-owned tool refresh."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping

from workshop.errors import StateConflict


_LEDGER = "host-corrections.jsonl"
_MAX_LEDGER_BYTES = 1024 * 1024
_MAX_RECORD_BYTES = 64 * 1024
_MAX_NOTICE_BYTES = 64 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
# Match AgentRun's existing materialized skill-name grammar, including older
# valid names with consecutive or trailing hyphens.
_SKILL = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_FIELDS = {"kind", "schema_version", "correction", "reason",
           "previous_checkpoint_sha256", "checkpoint_sha256", "changes"}
_CHANGE_FIELDS = {"path", "previous_sha256", "previous_mode", "sha256", "mode"}


def _fail() -> None:
    raise StateConflict("host tool refresh notice has invalid or stale evidence")


def _sha(value) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _identity(value):
    return value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns


def _ledger_bytes(host_state_root: Path) -> bytes | None:
    path = host_state_root / _LEDGER
    if not path.exists() and not path.is_symlink():
        return None
    try:
        before = path.lstat()
        if (
            host_state_root.is_symlink()
            or not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o600
            or not 1 <= before.st_size <= _MAX_LEDGER_BYTES
        ):
            _fail()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            if _identity(os.fstat(descriptor)) != _identity(before):
                _fail()
            chunks = []
            length = 0
            while length <= before.st_size:
                chunk = os.read(descriptor, min(64 * 1024, before.st_size + 1 - length))
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
            if _identity(os.fstat(descriptor)) != _identity(before):
                _fail()
        finally:
            os.close(descriptor)
        content = b"".join(chunks)
        if _identity(path.lstat()) != _identity(before) or len(content) != before.st_size:
            _fail()
    except OSError as exc:
        raise StateConflict("host tool refresh notice ledger is unavailable") from exc
    if not content.endswith(b"\n"):
        _fail()
    return content


def native_tool_refresh_notice(
    host_state_root: Path, input_sha256s: Mapping[str, str],
) -> str:
    """Describe only the latest completed refresh matching current bound inputs.

    No delivery claim is recorded: an interrupted continuation receives the
    same notice again. Missing records are not reconstructed, including the
    existing crash gap between a refresh checkpoint and its ledger append.
    Operator reasons, private paths and prior ledger history never reach the
    native prompt. This validates file identity, not engineering or readiness.
    """
    content = _ledger_bytes(host_state_root)
    if content is None:
        return ""
    latest = None
    try:
        for line in content.splitlines():
            if not line or len(line) > _MAX_RECORD_BYTES:
                _fail()
            record = json.loads(line, object_pairs_hook=_pairs,
                                parse_constant=lambda unused: _fail())
            if not isinstance(record, dict):
                _fail()
            if record.get("correction") == "domain-skill-refresh":
                latest = record
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise StateConflict("host tool refresh notice ledger is malformed") from exc
    if latest is None:
        return ""
    if (
        set(latest) != _FIELDS
        or latest["kind"] != "autonomous-workshop.host-correction"
        or type(latest["schema_version"]) is not int
        or latest["schema_version"] != 1
        or not isinstance(latest["reason"], str)
        or not 1 <= len(latest["reason"].strip()) <= 512
        or not _sha(latest["previous_checkpoint_sha256"])
        or not _sha(latest["checkpoint_sha256"])
        or latest["previous_checkpoint_sha256"] == latest["checkpoint_sha256"]
        or not isinstance(latest["changes"], list)
        or len(latest["changes"]) > 512
    ):
        _fail()
    changes = []
    seen = set()
    for change in latest["changes"]:
        if not isinstance(change, dict) or set(change) != _CHANGE_FIELDS:
            _fail()
        path = change["path"]
        if (
            not isinstance(path, str) or not 1 <= len(path) <= 1024
            or "\\" in path
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
        ):
            _fail()
        pure = PurePosixPath(path)
        if (
            pure.is_absolute() or pure.as_posix() != path or ".." in pure.parts
            or len(pure.parts) < 4 or pure.parts[:2] != (".agents", "skills")
            or _SKILL.fullmatch(pure.parts[2]) is None or path in seen
        ):
            _fail()
        seen.add(path)
        for prefix in ("previous_", ""):
            digest, mode = change[prefix + "sha256"], change[prefix + "mode"]
            if not ((digest is None and mode is None) or
                    (_sha(digest) and type(mode) is int and mode in (0o400, 0o500))):
                _fail()
        if (change["previous_sha256"], change["previous_mode"]) == (change["sha256"], change["mode"]):
            _fail()
        digest = change["sha256"]
        if digest is None:
            if path in input_sha256s:
                _fail()
        elif input_sha256s.get(path) != digest:
            _fail()
        changes.append({"path": path, "sha256": digest})
    if not changes:
        return ""
    identity = {"refresh_checkpoint_sha256": latest["checkpoint_sha256"],
                "changes": sorted(changes, key=lambda row: row["path"])}
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    notice = (
        "\n\nHost tool refresh notice (sha256=%s): %s\n"
        "These are the latest completed host refresh's exact paths and current "
        "manifest-bound hashes; a null hash means removed from the bound inputs. "
        "If this exact refresh revision has not yet been read, reread its changed "
        "SKILL.md and reference guidance before continuing affected work. Use "
        "the current run-local scripts and their applicable skill guidance; do "
        "not reuse a remembered interface for a changed tool or read removed files. "
        "Respect the frozen phase's skill deferrals; this notice does not activate "
        "a deferred skill. Continue the same Wish and current stage Goal. All "
        "engineering, review and finalization checks remain required."
        % (digest, encoded)
    )
    if len(notice.encode("utf-8")) > _MAX_NOTICE_BYTES:
        _fail()
    return notice
