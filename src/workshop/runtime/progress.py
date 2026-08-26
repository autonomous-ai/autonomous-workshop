"""Private, content-free progress metadata for one native product run.

The native event stream can contain prompts, reasoning, tool arguments, paths,
messages, and provider identities.  None of those bytes cross this boundary.
Only host-selected activity classes and checkpoint bindings are persisted.
Progress is diagnostic telemetry, never lifecycle or gate authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import ContractError


NATIVE_PROGRESS_KIND = "autonomous-workshop-native-progress"
NATIVE_PROGRESS_FILENAME = "native-progress.json"
MAX_NATIVE_PROGRESS_BYTES = 4 * 1024
SAFE_NATIVE_ACTIVITY_CLASSES = (
    "starting",
    "reasoning",
    "tool",
    "subagent",
    "finalizing",
    "completed",
    "failed",
)
_ACTIVE_ACTIVITY_CLASSES = frozenset(
    ("starting", "reasoning", "tool", "subagent", "finalizing")
)
_STAGES = frozenset(
    ("wish", "match", "invent", "make", "playtest", "release", "deliver")
)
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_COUNTER = 1_000_000
# Safely representable by ``datetime`` on supported POSIX hosts and centuries
# beyond the useful lifetime of a run, while rejecting hostile huge epochs.
_MAX_TIMESTAMP_MS = 10**13


class NativeProgressUnavailable(Exception):
    """The optional progress record cannot be trusted or used."""


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("native progress must be finite JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _timestamp(value_ms: int) -> str:
    return (
        datetime.fromtimestamp(value_ms / 1000, tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase sha256" % label)
    return value


def _require_stage(value: Any, label: str) -> str:
    if value not in _STAGES:
        raise ContractError("%s is invalid" % label)
    return value


def _require_counter(value: Any, label: str) -> int:
    if type(value) is not int or not 1 <= value <= _MAX_COUNTER:
        raise ContractError("%s is invalid" % label)
    return value


def _require_timestamp_ms(value: Any, label: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_TIMESTAMP_MS:
        raise ContractError("%s is invalid" % label)
    return value


@dataclass(frozen=True)
class NativeRunProgress:
    """One bounded progress snapshot bound to an authoritative checkpoint."""

    product_id: str
    wish_sha256: str
    checkpoint_sha256: str
    checkpoint_stage: str
    attempt_stage: str
    stage_attempt: int
    native_turns: int
    activity: str
    attempt_started_at_ms: int
    last_activity_at_ms: int
    schema_version: int = 1
    kind: str = NATIVE_PROGRESS_KIND

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.kind != NATIVE_PROGRESS_KIND:
            raise ContractError("native progress version is invalid")
        if (
            not isinstance(self.product_id, str)
            or _IDENTIFIER.fullmatch(self.product_id) is None
        ):
            raise ContractError("native progress product_id is invalid")
        _require_sha256(self.wish_sha256, "native progress Wish sha256")
        _require_sha256(
            self.checkpoint_sha256, "native progress checkpoint sha256"
        )
        _require_stage(self.checkpoint_stage, "native progress checkpoint stage")
        _require_stage(self.attempt_stage, "native progress attempt stage")
        _require_counter(self.stage_attempt, "native progress stage attempt")
        _require_counter(self.native_turns, "native progress turn count")
        if self.stage_attempt > self.native_turns:
            raise ContractError("native progress counters are inconsistent")
        if self.activity not in SAFE_NATIVE_ACTIVITY_CLASSES:
            raise ContractError("native progress activity is invalid")
        _require_timestamp_ms(
            self.attempt_started_at_ms,
            "native progress attempt timestamp",
        )
        _require_timestamp_ms(
            self.last_activity_at_ms,
            "native progress activity timestamp",
        )
        if self.last_activity_at_ms < self.attempt_started_at_ms:
            raise ContractError("native progress timestamps are inconsistent")

    def _core(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
            "checkpoint_stage": self.checkpoint_stage,
            "attempt_stage": self.attempt_stage,
            "stage_attempt": self.stage_attempt,
            "native_turns": self.native_turns,
            "activity": self.activity,
            "attempt_started_at_ms": self.attempt_started_at_ms,
            "last_activity_at_ms": self.last_activity_at_ms,
        }

    @property
    def progress_sha256(self) -> str:
        return _sha256(_canonical_json(self._core()))

    def to_dict(self) -> dict[str, Any]:
        return {**self._core(), "progress_sha256": self.progress_sha256}

    def observe(
        self,
        activity: str,
        *,
        observed_at_ms: Optional[int] = None,
    ) -> "NativeRunProgress":
        if activity not in SAFE_NATIVE_ACTIVITY_CLASSES:
            raise ContractError("native progress activity is invalid")
        observed = _now_ms() if observed_at_ms is None else observed_at_ms
        _require_timestamp_ms(observed, "native progress activity timestamp")
        return replace(
            self,
            activity=activity,
            last_activity_at_ms=max(
                self.last_activity_at_ms,
                self.attempt_started_at_ms,
                observed,
            ),
        )

    def rebind(
        self,
        *,
        checkpoint_sha256: str,
        checkpoint_stage: str,
        activity: Optional[str] = None,
        observed_at_ms: Optional[int] = None,
    ) -> "NativeRunProgress":
        updated = replace(
            self,
            checkpoint_sha256=_require_sha256(
                checkpoint_sha256,
                "native progress checkpoint sha256",
            ),
            checkpoint_stage=_require_stage(
                checkpoint_stage,
                "native progress checkpoint stage",
            ),
        )
        if activity is not None:
            updated = updated.observe(activity, observed_at_ms=observed_at_ms)
        return updated

    def public_view(self, *, observed_at_ms: Optional[int] = None) -> Mapping[str, Any]:
        now = _now_ms() if observed_at_ms is None else observed_at_ms
        _require_timestamp_ms(now, "native progress observation timestamp")
        terminal = self.activity not in _ACTIVE_ACTIVITY_CLASSES
        end = self.last_activity_at_ms if terminal else max(now, self.last_activity_at_ms)
        elapsed_seconds = max(0, end - self.attempt_started_at_ms) // 1000
        return {
            "status": "available",
            "stage_attempt": {
                "stage": self.attempt_stage,
                "number": self.stage_attempt,
            },
            "activity": self.activity,
            "elapsed_seconds": elapsed_seconds,
            "last_activity_at": _timestamp(self.last_activity_at_ms),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeRunProgress":
        expected = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "checkpoint_sha256",
            "checkpoint_stage",
            "attempt_stage",
            "stage_attempt",
            "native_turns",
            "activity",
            "attempt_started_at_ms",
            "last_activity_at_ms",
            "progress_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native progress fields are invalid")
        progress_sha256 = _require_sha256(
            value["progress_sha256"], "native progress sha256"
        )
        progress = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            product_id=value["product_id"],
            wish_sha256=value["wish_sha256"],
            checkpoint_sha256=value["checkpoint_sha256"],
            checkpoint_stage=value["checkpoint_stage"],
            attempt_stage=value["attempt_stage"],
            stage_attempt=value["stage_attempt"],
            native_turns=value["native_turns"],
            activity=value["activity"],
            attempt_started_at_ms=value["attempt_started_at_ms"],
            last_activity_at_ms=value["last_activity_at_ms"],
        )
        if progress.progress_sha256 != progress_sha256:
            raise ContractError("native progress digest does not match its bytes")
        return progress


def begin_native_progress(
    previous: Optional[NativeRunProgress],
    *,
    product_id: str,
    wish_sha256: str,
    checkpoint_sha256: str,
    checkpoint_stage: str,
    started_at_ms: Optional[int] = None,
) -> NativeRunProgress:
    """Start and durably count one attempted native turn."""

    started = _now_ms() if started_at_ms is None else started_at_ms
    _require_timestamp_ms(started, "native progress attempt timestamp")
    if previous is not None and (
        previous.product_id != product_id
        or previous.wish_sha256 != wish_sha256
        or previous.checkpoint_sha256 != checkpoint_sha256
        or previous.checkpoint_stage != checkpoint_stage
    ):
        previous = None
    native_turns = 1 if previous is None else previous.native_turns + 1
    stage_attempt = (
        previous.stage_attempt + 1
        if previous is not None and previous.attempt_stage == checkpoint_stage
        else 1
    )
    return NativeRunProgress(
        product_id=product_id,
        wish_sha256=wish_sha256,
        checkpoint_sha256=checkpoint_sha256,
        checkpoint_stage=checkpoint_stage,
        attempt_stage=checkpoint_stage,
        stage_attempt=stage_attempt,
        native_turns=native_turns,
        activity="starting",
        attempt_started_at_ms=started,
        last_activity_at_ms=started,
    )


def write_native_progress(path: Path, progress: NativeRunProgress) -> None:
    """Atomically replace one private progress record without following links."""

    if not isinstance(progress, NativeRunProgress):
        raise ContractError("native progress writer requires a progress record")
    content = _canonical_json(progress.to_dict()) + b"\n"
    if len(content) > MAX_NATIVE_PROGRESS_BYTES:
        raise ContractError("native progress exceeded its safe size limit")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        directory = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_native_progress(path: Path) -> NativeRunProgress:
    """Read one private progress record without following or trusting links."""

    try:
        expected = path.lstat()
    except OSError as exc:
        raise NativeProgressUnavailable("native progress is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(expected.st_mode)
        or stat.S_IMODE(expected.st_mode) != 0o600
        or not 1 <= expected.st_size <= MAX_NATIVE_PROGRESS_BYTES
    ):
        raise NativeProgressUnavailable("native progress is unavailable")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise NativeProgressUnavailable("native progress is unavailable") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or stat.S_IMODE(opened.st_mode) != 0o600
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise NativeProgressUnavailable("native progress is unavailable")
        content = os.read(descriptor, MAX_NATIVE_PROGRESS_BYTES + 1)
        if len(content) > MAX_NATIVE_PROGRESS_BYTES or os.read(descriptor, 1):
            raise NativeProgressUnavailable("native progress is unavailable")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise NativeProgressUnavailable("native progress is unavailable")
    except OSError as exc:
        raise NativeProgressUnavailable("native progress is unavailable") from exc
    finally:
        os.close(descriptor)
    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=_strict_object
        )
        return NativeRunProgress.from_mapping(value)
    except (UnicodeError, ValueError, json.JSONDecodeError, ContractError) as exc:
        raise NativeProgressUnavailable("native progress is unavailable") from exc


def trusted_native_progress(
    path: Path,
    *,
    product_id: str,
    wish_sha256: str,
    checkpoint_sha256: str,
    checkpoint_stage: str,
) -> Optional[NativeRunProgress]:
    """Return progress only when every run/checkpoint binding is exact."""

    try:
        progress = read_native_progress(path)
    except NativeProgressUnavailable:
        return None
    if (
        progress.product_id != product_id
        or progress.wish_sha256 != wish_sha256
        or progress.checkpoint_sha256 != checkpoint_sha256
        or progress.checkpoint_stage != checkpoint_stage
    ):
        return None
    return progress


__all__ = [
    "MAX_NATIVE_PROGRESS_BYTES",
    "NATIVE_PROGRESS_FILENAME",
    "NATIVE_PROGRESS_KIND",
    "SAFE_NATIVE_ACTIVITY_CLASSES",
    "NativeProgressUnavailable",
    "NativeRunProgress",
    "begin_native_progress",
    "read_native_progress",
    "trusted_native_progress",
    "write_native_progress",
]
