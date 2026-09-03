"""One daydream-and-build loop per Inventor, stoppable from another terminal.

``workshop start <inventor>`` dreams and builds until it is stopped.  The loop
holds one lease file per Inventor so two loops never dream for the same
Inventor at once, and it checks for a stop marker between steps so
``workshop stop <inventor>`` can end it cleanly after the current step.
"""

from __future__ import annotations

import json
import os
import signal
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from workshop.daydream._files import read_regular_bytes, write_private_bytes
from workshop.daydream.contracts import (
    CREATED_AT_FORMAT,
    DaydreamError,
    canonical_json,
    require_created_at,
    require_daydream_id,
    require_inventor_id,
)
from workshop.daydream.native import _inventor_daydreams
from workshop.errors import ContractError


LOOP_KIND = "autonomous-workshop.daydream-loop"
LOOP_FILE_NAME = "LOOP.json"
STOP_FILE_NAME = "STOP"
MAX_LOOP_FILE_BYTES = 64 * 1024
MAX_REASON_CHARS = 500
LOOP_STATUSES = ("running", "stopped")
DEFAULT_MAX_CONSECUTIVE_FAILURES = 3
_LOOP_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "inventor_id",
        "pid",
        "started_at",
        "updated_at",
        "status",
        "ideas",
        "builds",
        "published",
        "consecutive_failures",
        "last_daydream_id",
        "last_wish_id",
        "stop_reason",
    )
)


def _now(moment: Optional[datetime]) -> str:
    observed = moment if moment is not None else datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc).strftime(CREATED_AT_FORMAT)


def _count(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError("loop %s must be a non-negative integer" % label)
    return value


@dataclass(frozen=True, kw_only=True)
class LoopState:
    """The durable, owner-only record of one Inventor's loop."""

    schema_version: int = 1
    inventor_id: str
    pid: int
    started_at: str
    updated_at: str
    status: str
    ideas: int = 0
    builds: int = 0
    published: int = 0
    consecutive_failures: int = 0
    last_daydream_id: Optional[str] = None
    last_wish_id: Optional[str] = None
    stop_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("loop schema_version must be 1")
        require_inventor_id(self.inventor_id, "loop inventor_id")
        if type(self.pid) is not int or self.pid <= 0:
            raise ContractError("loop pid must be a positive integer")
        require_created_at(self.started_at, "loop started_at")
        require_created_at(self.updated_at, "loop updated_at")
        if self.status not in LOOP_STATUSES:
            raise ContractError("loop status must be one of %s" % (LOOP_STATUSES,))
        for name in ("ideas", "builds", "published", "consecutive_failures"):
            _count(getattr(self, name), name)
        if self.last_daydream_id is not None:
            require_daydream_id(self.last_daydream_id, "loop last_daydream_id")
        if self.last_wish_id is not None and (
            not isinstance(self.last_wish_id, str)
            or not self.last_wish_id.strip()
            or len(self.last_wish_id) > 256
        ):
            raise ContractError("loop last_wish_id is invalid")
        if self.stop_reason is not None and (
            not isinstance(self.stop_reason, str)
            or not self.stop_reason.strip()
            or len(self.stop_reason) > MAX_REASON_CHARS
            or any(ord(character) < 32 for character in self.stop_reason)
        ):
            raise ContractError("loop stop_reason is invalid")

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "LoopState":
        if not isinstance(raw, Mapping) or set(raw) != _LOOP_KEYS:
            raise ContractError("loop record has the wrong keys")
        if raw["kind"] != LOOP_KIND:
            raise ContractError("loop kind must be %s" % LOOP_KIND)
        values = {key: raw[key] for key in _LOOP_KEYS if key != "kind"}
        return cls(**values)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": LOOP_KIND,
            "inventor_id": self.inventor_id,
            "pid": self.pid,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "ideas": self.ideas,
            "builds": self.builds,
            "published": self.published,
            "consecutive_failures": self.consecutive_failures,
            "last_daydream_id": self.last_daydream_id,
            "last_wish_id": self.last_wish_id,
            "stop_reason": self.stop_reason,
        }


def pid_alive(pid: int) -> bool:
    """Whether a process id currently exists; permission errors count as alive."""

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_loop_state(path: Path) -> Optional[LoopState]:
    """Return the loop record at ``path``; absent or malformed records read as None."""

    try:
        payload = read_regular_bytes(path, maximum=MAX_LOOP_FILE_BYTES, label="daydream loop")
    except FileNotFoundError:
        return None
    except DaydreamError:
        return None
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    try:
        return LoopState.parse(raw)
    except ContractError:
        return None


def _write_loop_state(path: Path, state: LoopState) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    write_private_bytes(
        temporary,
        (canonical_json(state.to_dict()) + "\n").encode("utf-8"),
        label="daydream loop record",
    )
    os.replace(temporary, path)


class LoopLease:
    """The running loop's handle on its record and stop marker."""

    def __init__(self, folder: Path, state: LoopState) -> None:
        self.folder = folder
        self.state = state

    @property
    def path(self) -> Path:
        return self.folder / LOOP_FILE_NAME

    @property
    def stop_path(self) -> Path:
        return self.folder / STOP_FILE_NAME

    def update(self, *, moment: Optional[datetime] = None, **fields: Any) -> LoopState:
        self.state = replace(self.state, updated_at=_now(moment), **fields)
        _write_loop_state(self.path, self.state)
        return self.state

    def stop_requested(self) -> bool:
        return self.stop_path.exists() or self.stop_path.is_symlink()

    def release(self, *, reason: str, moment: Optional[datetime] = None) -> LoopState:
        state = self.update(moment=moment, status="stopped", stop_reason=reason)
        try:
            self.stop_path.unlink()
        except FileNotFoundError:
            pass
        return state


def acquire_loop(
    inventor_id: str,
    *,
    home: Optional[Path] = None,
    pid: Optional[int] = None,
    moment: Optional[datetime] = None,
    alive: Callable[[int], bool] = pid_alive,
) -> LoopLease:
    """Take the one loop lease for an Inventor; a live loop elsewhere fails closed."""

    inventor_id = require_inventor_id(inventor_id)
    folder = _inventor_daydreams(inventor_id, home=home, create=True)
    path = folder / LOOP_FILE_NAME
    own_pid = pid if pid is not None else os.getpid()
    existing = read_loop_state(path)
    if (
        existing is not None
        and existing.status == "running"
        and existing.pid != own_pid
        and alive(existing.pid)
    ):
        raise DaydreamError(
            "a daydream loop for %s is already running (pid %d); stop it with "
            "`workshop stop %s`" % (inventor_id, existing.pid, inventor_id)
        )
    stamp = _now(moment)
    state = LoopState(
        inventor_id=inventor_id,
        pid=own_pid,
        started_at=stamp,
        updated_at=stamp,
        status="running",
    )
    _write_loop_state(path, state)
    lease = LoopLease(folder, state)
    try:
        # A marker left by a stop request for a previous, now dead loop must
        # not end this one before it starts.
        lease.stop_path.unlink()
    except FileNotFoundError:
        pass
    return lease


def request_stop(
    inventor_id: str,
    *,
    home: Optional[Path] = None,
    now: bool = False,
    alive: Callable[[int], bool] = pid_alive,
    signaller: Callable[[int, int], None] = os.kill,
) -> LoopState:
    """Ask the running loop to end after its step; ``now`` also interrupts it."""

    inventor_id = require_inventor_id(inventor_id)
    try:
        folder = _inventor_daydreams(inventor_id, home=home, create=False)
    except DaydreamError as exc:
        raise DaydreamError("no daydream loop is running for %s" % inventor_id) from exc
    state = read_loop_state(folder / LOOP_FILE_NAME)
    if state is None or state.status != "running" or not alive(state.pid):
        raise DaydreamError("no daydream loop is running for %s" % inventor_id)
    stop_path = folder / STOP_FILE_NAME
    if not (stop_path.exists() or stop_path.is_symlink()):
        write_private_bytes(stop_path, b"stop\n", label="daydream stop marker")
    if now:
        signaller(state.pid, signal.SIGINT)
    return state


__all__ = [
    "DEFAULT_MAX_CONSECUTIVE_FAILURES",
    "LOOP_FILE_NAME",
    "LOOP_KIND",
    "STOP_FILE_NAME",
    "LoopLease",
    "LoopState",
    "acquire_loop",
    "pid_alive",
    "read_loop_state",
    "request_stop",
]
