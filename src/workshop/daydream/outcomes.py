"""Route-independent host-observed outcome memory for later Daydreams."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from workshop._validation import require_sha256
from workshop.daydream._files import append_private_line, read_regular_bytes
from workshop.daydream.contracts import (
    CREATED_AT_FORMAT,
    DaydreamError,
    bounded_line,
    bounded_paragraph,
    canonical_json,
    require_created_at,
    require_daydream_id,
    require_inventor_id,
)
from workshop.errors import ContractError
from workshop.runtime.package_data import default_workshop_home
from workshop.wish import Wish


OUTCOME_MEMORY_KIND = "autonomous-workshop.daydream-run-outcome"
OUTCOME_FILE_NAME = "OUTCOMES.jsonl"
MAX_OUTCOME_MEMORY_BYTES = 16 * 1024 * 1024
MAX_OUTCOME_LINE_BYTES = 16 * 1024
DEFAULT_OUTCOME_LIMIT = 500
_OUTCOME_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "event_sha256",
        "daydream_id",
        "idea_sha256",
        "wish_id",
        "recorded_at",
        "result",
        "route",
        "manager",
        "run_status",
        "stage",
        "revision",
        "round",
        "wish_sha256",
        "checkpoint_sha256",
        "publication_status",
        "publication_verified",
        "error_type",
        "error_detail",
    )
)


def _optional_line(value: Any, label: str, maximum: int) -> Optional[str]:
    if value is None:
        return None
    return bounded_line(value, label, maximum)


def _optional_sha256(value: Any, label: str) -> Optional[str]:
    if value is None:
        return None
    return require_sha256(value, label)


def _optional_nonnegative_int(value: Any, label: str) -> Optional[int]:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ContractError("%s must be a non-negative integer or null" % label)
    return value


def _optional_bool(value: Any, label: str) -> Optional[bool]:
    if value is None:
        return None
    if type(value) is not bool:
        raise ContractError("%s must be a boolean or null" % label)
    return value


@dataclass(frozen=True)
class RunOutcomeMemory:
    """One bounded event; receipt fields are observations, never reward scores."""

    daydream_id: str
    idea_sha256: str
    wish_id: str
    recorded_at: str
    result: str
    route: Optional[str]
    manager: Optional[str]
    run_status: Optional[str]
    stage: Optional[str]
    revision: Optional[int]
    round: Optional[int]
    wish_sha256: Optional[str]
    checkpoint_sha256: Optional[str]
    publication_status: Optional[str]
    publication_verified: Optional[bool]
    error_type: Optional[str]
    error_detail: Optional[str]

    def __post_init__(self) -> None:
        require_daydream_id(self.daydream_id, "outcome daydream_id")
        require_sha256(self.idea_sha256, "outcome idea_sha256")
        bounded_line(self.wish_id, "outcome wish_id", 256)
        if any(character in "/\\" for character in self.wish_id):
            raise ContractError("outcome wish_id must not contain path separators")
        require_created_at(self.recorded_at, "outcome recorded_at")
        if self.result not in ("receipt", "error", "interrupted"):
            raise ContractError("outcome result must be receipt, error, or interrupted")
        for value, label, maximum in (
            (self.route, "outcome route", 32),
            (self.manager, "outcome manager", 32),
            (self.run_status, "outcome run_status", 32),
            (self.stage, "outcome stage", 32),
            (self.publication_status, "outcome publication_status", 32),
            (self.error_type, "outcome error_type", 200),
        ):
            _optional_line(value, label, maximum)
        _optional_nonnegative_int(self.revision, "outcome revision")
        _optional_nonnegative_int(self.round, "outcome round")
        _optional_sha256(self.wish_sha256, "outcome wish_sha256")
        _optional_sha256(self.checkpoint_sha256, "outcome checkpoint_sha256")
        _optional_bool(self.publication_verified, "outcome publication_verified")
        if self.error_detail is not None:
            bounded_paragraph(self.error_detail, "outcome error_detail", 1_000)
        if self.result == "receipt" and any(
            value is not None for value in (self.error_type, self.error_detail)
        ):
            raise ContractError("receipt outcome cannot carry an error")
        if self.result != "receipt" and (
            self.error_type is None or self.error_detail is None
        ):
            raise ContractError("error outcome must retain its type and detail")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": OUTCOME_MEMORY_KIND,
            "daydream_id": self.daydream_id,
            "idea_sha256": self.idea_sha256,
            "wish_id": self.wish_id,
            "recorded_at": self.recorded_at,
            "result": self.result,
            "route": self.route,
            "manager": self.manager,
            "run_status": self.run_status,
            "stage": self.stage,
            "revision": self.revision,
            "round": self.round,
            "wish_sha256": self.wish_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
            "publication_status": self.publication_status,
            "publication_verified": self.publication_verified,
            "error_type": self.error_type,
            "error_detail": self.error_detail,
        }

    @property
    def event_sha256(self) -> str:
        return hashlib.sha256(
            canonical_json(self._content_dict()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        value = self._content_dict()
        value["event_sha256"] = self.event_sha256
        return value

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "RunOutcomeMemory":
        if not isinstance(raw, Mapping) or set(raw) != _OUTCOME_KEYS:
            raise ContractError(
                "outcome memory keys must be exactly %s" % sorted(_OUTCOME_KEYS)
            )
        if (
            type(raw["schema_version"]) is not int
            or raw["schema_version"] != 1
            or raw["kind"] != OUTCOME_MEMORY_KIND
        ):
            raise ContractError("outcome memory identity is invalid")
        event_sha256 = require_sha256(raw["event_sha256"], "outcome event_sha256")
        identity_keys = {"schema_version", "kind", "event_sha256"}
        memory = cls(
            **{name: raw[name] for name in _OUTCOME_KEYS if name not in identity_keys}
        )
        if memory.event_sha256 != event_sha256:
            raise ContractError("outcome event_sha256 does not match its exact facts")
        return memory


def _private_directory(path: Path, *, label: str) -> Path:
    created = False
    try:
        path.mkdir(mode=0o700)
        created = True
    except FileExistsError:
        pass
    except OSError as exc:
        raise DaydreamError("cannot create %s: %s" % (label, path)) from exc
    identity = path.lstat()
    if path.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise DaydreamError("%s must be a real directory: %s" % (label, path))
    if created:
        os.chmod(path, 0o700)
    elif stat.S_IMODE(identity.st_mode) != 0o700:
        raise DaydreamError("%s permissions must be 0700: %s" % (label, path))
    return path


def outcome_path(inventor_id: str, *, home: Optional[Path] = None) -> Path:
    """Resolve the private per-Inventor outcome log, creating safe parents."""

    inventor_id = require_inventor_id(inventor_id)
    root = Path(home) if home is not None else Path(default_workshop_home())
    if not root.is_absolute():
        raise ContractError("Workshop home must be absolute")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        identity = root.lstat()
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise DaydreamError("Workshop home is unavailable: %s" % root) from exc
    if root.is_symlink() or not stat.S_ISDIR(identity.st_mode) or resolved != root:
        raise DaydreamError("Workshop home must be a real canonical directory: %s" % root)
    daydreams = _private_directory(root / "daydreams", label="daydreams directory")
    owner = _private_directory(daydreams / inventor_id, label="Inventor memory directory")
    return owner / OUTCOME_FILE_NAME


def _origin(wish: Wish) -> Optional[tuple[str, str, str]]:
    if not isinstance(wish, Wish):
        raise ContractError("outcome memory requires a Wish")
    context = wish.context
    if context.get("source") != "workshop-daydream":
        return None
    inventor_id = require_inventor_id(context.get("inventor_id"), "Wish inventor_id")
    daydream_id = require_daydream_id(context.get("daydream_id"), "Wish daydream_id")
    idea_sha256 = require_sha256(context.get("idea_sha256"), "Wish idea_sha256")
    return inventor_id, daydream_id, idea_sha256


def remember_run_outcome(
    wish: Wish,
    *,
    receipt: Optional[Mapping[str, Any]] = None,
    error: Optional[BaseException] = None,
    route: Optional[str] = None,
    manager: Optional[str] = None,
    moment: Optional[datetime] = None,
    home: Optional[Path] = None,
) -> bool:
    """Append one allowlisted host observation for a Daydream-originated Wish."""

    origin = _origin(wish)
    if origin is None:
        return False
    if (receipt is None) == (error is None):
        raise ContractError("outcome memory requires exactly one receipt or error")
    observed = moment if moment is not None else datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    recorded_at = observed.astimezone(timezone.utc).strftime(CREATED_AT_FORMAT)
    publication: Mapping[str, Any] = {}
    if receipt is not None:
        if not isinstance(receipt, Mapping):
            raise ContractError("run receipt must be a mapping")
        candidate = receipt.get("publication")
        if isinstance(candidate, Mapping):
            publication = candidate
        result = "receipt"
        error_type = error_detail = None
    else:
        result = "interrupted" if isinstance(error, KeyboardInterrupt) else "error"
        error_type = type(error).__name__
        error_detail = str(error) or error_type
        receipt = {}
    inventor_id, daydream_id, idea_sha256 = origin
    memory = RunOutcomeMemory(
        daydream_id=daydream_id,
        idea_sha256=idea_sha256,
        wish_id=wish.product_id,
        recorded_at=recorded_at,
        result=result,
        route=_optional_line(receipt.get("effort") or route, "outcome route", 32),
        manager=_optional_line(receipt.get("manager") or manager, "outcome manager", 32),
        run_status=_optional_line(receipt.get("status"), "outcome run_status", 32),
        stage=_optional_line(receipt.get("stage"), "outcome stage", 32),
        revision=_optional_nonnegative_int(receipt.get("revision"), "outcome revision"),
        round=_optional_nonnegative_int(receipt.get("round"), "outcome round"),
        wish_sha256=_optional_sha256(receipt.get("wish_sha256"), "outcome wish_sha256"),
        checkpoint_sha256=_optional_sha256(
            receipt.get("checkpoint_sha256"), "outcome checkpoint_sha256"
        ),
        publication_status=_optional_line(
            publication.get("status"), "outcome publication_status", 32
        ),
        publication_verified=_optional_bool(
            publication.get("verified"), "outcome publication_verified"
        ),
        error_type=error_type,
        error_detail=error_detail,
    )
    line = (canonical_json(memory.to_dict()) + "\n").encode("utf-8")
    if len(line) > MAX_OUTCOME_LINE_BYTES:
        raise ContractError("outcome memory entry exceeds its byte bound")
    append_private_line(
        outcome_path(inventor_id, home=home), line, label="Daydream outcome memory"
    )
    return True


def read_outcomes(
    path: Path, *, limit: int = DEFAULT_OUTCOME_LIMIT
) -> tuple[RunOutcomeMemory, ...]:
    if type(limit) is not int or limit < 1:
        raise ContractError("outcome limit must be a positive integer")
    try:
        payload = read_regular_bytes(
            Path(path), maximum=MAX_OUTCOME_MEMORY_BYTES, label="Daydream outcome memory"
        )
    except FileNotFoundError:
        return ()
    memories: list[RunOutcomeMemory] = []
    for line in payload.split(b"\n"):
        if not line.strip() or len(line) > MAX_OUTCOME_LINE_BYTES:
            continue
        try:
            raw = json.loads(line.decode("utf-8"))
            memories.append(RunOutcomeMemory.parse(raw))
        except (UnicodeError, ValueError, RecursionError, ContractError):
            continue
    return tuple(memories[-limit:])


def render_outcomes_markdown(outcomes: Sequence[RunOutcomeMemory]) -> str:
    lines = ["# Downstream outcomes (host-observed facts, not Judge predictions)", ""]
    if not outcomes:
        lines.append("(none recorded yet)")
    for outcome in outcomes:
        if not isinstance(outcome, RunOutcomeMemory):
            raise ContractError("render_outcomes_markdown requires RunOutcomeMemory items")
        if outcome.result == "receipt":
            lines.append(
                "- %s -> %s: route=%s status=%s stage=%s publication=%s"
                % (
                    outcome.daydream_id,
                    outcome.wish_id,
                    outcome.route or "unknown",
                    outcome.run_status or "unknown",
                    outcome.stage or "unknown",
                    outcome.publication_status or "unknown",
                )
            )
        else:
            lines.append(
                "- %s -> %s: %s %s: %s"
                % (
                    outcome.daydream_id,
                    outcome.wish_id,
                    outcome.result,
                    outcome.error_type,
                    outcome.error_detail,
                )
            )
    return "\n".join(lines) + "\n"


__all__ = [
    "DEFAULT_OUTCOME_LIMIT",
    "MAX_OUTCOME_MEMORY_BYTES",
    "OUTCOME_FILE_NAME",
    "OUTCOME_MEMORY_KIND",
    "RunOutcomeMemory",
    "outcome_path",
    "read_outcomes",
    "remember_run_outcome",
    "render_outcomes_markdown",
]
