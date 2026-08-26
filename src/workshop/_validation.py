"""Private validation helpers shared by Workshop contracts.

The component packages own their public records.  This module contains only
small, stateless validators so those records can share the exact same
persisted-value checks without depending on a cross-component model hub.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Optional

from workshop.errors import ContractError


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
MAX_EVIDENCE_JSON_BYTES = 2 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_utc_timestamp(value: str, label: str = "timestamp") -> str:
    if not isinstance(value, str):
        raise ContractError("%s must be an ISO-8601 UTC timestamp" % label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("%s must be an ISO-8601 UTC timestamp" % label) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ContractError("%s must include an explicit UTC offset" % label)
    return value


def require_exact_version(value: str, label: str = "version") -> str:
    floating = {
        "latest",
        "main",
        "master",
        "head",
        "dev",
        "development",
        "unknown",
        "snapshot",
        "x",
    }
    if (
        not isinstance(value, str)
        or not _EXACT_VERSION.fullmatch(value)
        or not any(character.isdigit() for character in value)
        or any(
            segment in floating
            for segment in re.split(r"[._+-]", value.casefold())
        )
    ):
        raise ContractError("%s must be an exact, non-floating version" % label)
    return value


def require_safe_evidence_path(value: str, label: str = "evidence_ref") -> str:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or not candidate.parts
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return value


def require_sha256(value: str, label: str = "sha256") -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContractError("%s must be 64 lowercase hexadecimal characters" % label)
    return value


def require_json_mapping(
    value: Mapping[str, Any],
    label: str,
    maximum_bytes: int = MAX_EVIDENCE_JSON_BYTES,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("%s must be an object" % label)

    def normalize(item: Any, depth: int = 0, active: Optional[set] = None) -> Any:
        if depth > 64:
            raise ContractError("%s exceeds the JSON nesting limit" % label)
        active = active if active is not None else set()
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            if item != item or item in (float("inf"), float("-inf")):
                raise ContractError("%s must contain only finite JSON numbers" % label)
            return item
        if isinstance(item, Mapping):
            if not all(isinstance(key, str) for key in item):
                raise ContractError("%s object keys must be strings" % label)
            identity = id(item)
            if identity in active:
                raise ContractError("%s must not contain cycles" % label)
            active.add(identity)
            try:
                return {
                    key: normalize(nested, depth + 1, active)
                    for key, nested in item.items()
                }
            finally:
                active.remove(identity)
        if isinstance(item, (list, tuple)):
            identity = id(item)
            if identity in active:
                raise ContractError("%s must not contain cycles" % label)
            active.add(identity)
            try:
                return [normalize(nested, depth + 1, active) for nested in item]
            finally:
                active.remove(identity)
        raise ContractError("%s contains a non-JSON value" % label)

    normalized = normalize(value)
    payload = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    if len(payload) > maximum_bytes:
        raise ContractError("%s exceeds the %d-byte limit" % (label, maximum_bytes))
    return value


def bounded_text(value: Any, label: str, maximum: int = 10_000) -> str:
    """Validate persisted human-readable text using the original job rules."""

    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(
            ord(character) < 32 and character not in "\n\r\t"
            for character in value
        )
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty text" % label)
    return value


def copy_json_mapping(
    value: Mapping[str, Any], label: str, *, nonempty: bool = False
) -> Dict[str, Any]:
    """Return a detached, normalized JSON object for a frozen record."""

    require_json_mapping(value, label)
    try:
        copied = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("%s must be a JSON object" % label) from exc
    if nonempty and not copied:
        raise ContractError("%s must not be empty" % label)
    return copied


__all__ = [
    "MAX_EVIDENCE_JSON_BYTES",
    "bounded_text",
    "copy_json_mapping",
    "require_exact_version",
    "require_json_mapping",
    "require_safe_evidence_path",
    "require_sha256",
    "require_utc_timestamp",
    "utc_now",
]
