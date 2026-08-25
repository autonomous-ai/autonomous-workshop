"""An immutable provenance mark for one inventor Make run.

``MakerMark`` records how a candidate was made.  It deliberately says nothing
about whether that candidate is beautiful, printable, inspected, or ready to
produce.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from workshop.errors import ContractError
from workshop._validation import require_exact_version, require_sha256, require_utc_timestamp


MAKER_MARK_MODES = ("live", "fixture", "offline", "replay")
MAX_MAKER_MARK_JSON_BYTES = 256 * 1024

_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_TOOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_INPUT_NAME = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|\+00:00)$"
)


def _require_cost(value: int, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError("%s must be a non-negative integer" % label)
    return value


def _freeze_inputs(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or not value:
        raise ContractError("maker mark input_sha256 must be a non-empty object")
    if len(value) > 128:
        raise ContractError("maker mark input_sha256 exceeds 128 entries")
    copied: Dict[str, str] = {}
    for name, digest in value.items():
        if not isinstance(name, str) or not _INPUT_NAME.fullmatch(name):
            raise ContractError("maker mark input names must be stable lowercase ids")
        require_sha256(digest, "maker mark input_sha256[%s]" % name)
        copied[name] = digest
    return MappingProxyType(dict(sorted(copied.items())))


def _freeze_limitations(value: Sequence[str]) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("maker mark limitations must be an array")
    if len(value) > 100:
        raise ContractError("maker mark limitations exceeds 100 entries")
    copied = []
    for limitation in value:
        if (
            not isinstance(limitation, str)
            or not limitation.strip()
            or len(limitation) > 2_000
            or any(ord(character) < 32 or ord(character) == 127 for character in limitation)
        ):
            raise ContractError(
                "maker mark limitations must be bounded, non-empty, control-free strings"
            )
        copied.append(limitation)
    if len(copied) != len(set(copied)):
        raise ContractError("maker mark limitations must be unique")
    return tuple(copied)


def _utc_datetime(value: str, label: str) -> datetime:
    require_utc_timestamp(value, label)
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise ContractError("%s must use RFC-3339 UTC form" % label)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class MakerMark:
    """Exact execution provenance for one candidate-making run.

    A live mode describes execution, not quality. Only
    :attr:`may_claim_live_creation` authorizes the narrower statement that an
    authenticated live agent tool made the candidate.
    """

    schema_version: int
    inventor_id: str
    run_id: str
    mode: str
    tool: str
    tool_version: str
    authenticated: bool
    taste_sha256: str
    artifact_sha256: str
    input_sha256: Mapping[str, str]
    agent_calls: int
    actual_cost_micros: int
    synthetic_cost_micros: int
    started_at: str
    completed_at: str
    limitations: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_sha256", _freeze_inputs(self.input_sha256))
        object.__setattr__(self, "limitations", _freeze_limitations(self.limitations))
        self.assert_valid()

    @property
    def is_live(self) -> bool:
        """Whether the recorded tool mode was live, authenticated or not."""

        return self.mode == "live"

    @property
    def may_claim_live_creation(self) -> bool:
        """Whether this mark supports a live claim for its named artifact.

        Consumers must also call :meth:`assert_artifact` with the product they
        are evaluating.  A mark copied beside different bytes is not evidence
        for those bytes.
        """

        return (
            self.is_live
            and self.authenticated
            and self.agent_calls > 0
            and self.synthetic_cost_micros == 0
        )

    def assert_artifact(self, artifact_sha256: str) -> None:
        """Require this mark to belong to the selected product bytes."""

        require_sha256(artifact_sha256, "maker mark selected artifact_sha256")
        if self.artifact_sha256 != artifact_sha256:
            raise ContractError("maker mark belongs to different artifact bytes")

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("maker mark schema_version must be 1")
        if not isinstance(self.inventor_id, str) or not _INVENTOR_ID.fullmatch(
            self.inventor_id
        ):
            raise ContractError("maker mark inventor_id must be a canonical inventor id")
        if not isinstance(self.run_id, str) or not _RUN_ID.fullmatch(self.run_id):
            raise ContractError("maker mark run_id must be a stable run id")
        if self.mode not in MAKER_MARK_MODES:
            raise ContractError(
                "maker mark mode must be live, fixture, offline, or replay"
            )
        if not isinstance(self.tool, str) or not _TOOL.fullmatch(self.tool):
            raise ContractError("maker mark tool must be a stable tool id")
        require_exact_version(self.tool_version, "maker mark tool_version")
        if type(self.authenticated) is not bool:
            raise ContractError("maker mark authenticated must be boolean")
        require_sha256(self.taste_sha256, "maker mark taste_sha256")
        require_sha256(self.artifact_sha256, "maker mark artifact_sha256")
        _freeze_inputs(self.input_sha256)
        if type(self.agent_calls) is not int or self.agent_calls < 0:
            raise ContractError("maker mark agent_calls must be a non-negative integer")
        _require_cost(self.actual_cost_micros, "maker mark actual_cost_micros")
        _require_cost(self.synthetic_cost_micros, "maker mark synthetic_cost_micros")
        started = _utc_datetime(self.started_at, "maker mark started_at")
        completed = _utc_datetime(self.completed_at, "maker mark completed_at")
        if completed < started:
            raise ContractError("maker mark completed_at must not precede started_at")
        _freeze_limitations(self.limitations)

        if self.is_live:
            if self.synthetic_cost_micros != 0:
                raise ContractError("a live maker mark cannot report synthetic cost")
        else:
            if self.authenticated:
                raise ContractError("a non-live maker mark cannot be authenticated")
            if self.actual_cost_micros != 0:
                raise ContractError("a non-live maker mark cannot report actual cost")
        if not self.may_claim_live_creation and not self.limitations:
            raise ContractError(
                "a maker mark that cannot claim live creation must state a limitation"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Return a fresh JSON-compatible representation."""

        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "inventor_id": self.inventor_id,
            "run_id": self.run_id,
            "mode": self.mode,
            "tool": self.tool,
            "tool_version": self.tool_version,
            "authenticated": self.authenticated,
            "taste_sha256": self.taste_sha256,
            "artifact_sha256": self.artifact_sha256,
            "input_sha256": dict(self.input_sha256),
            "agent_calls": self.agent_calls,
            "actual_cost_micros": self.actual_cost_micros,
            "synthetic_cost_micros": self.synthetic_cost_micros,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "limitations": list(self.limitations),
        }

    def to_json(self) -> str:
        """Return stable compact JSON suitable for ``maker-mark.json``."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MakerMark":
        if not isinstance(value, Mapping):
            raise ContractError("maker mark must be an object")
        expected = {
            "schema_version",
            "inventor_id",
            "run_id",
            "mode",
            "tool",
            "tool_version",
            "authenticated",
            "taste_sha256",
            "artifact_sha256",
            "input_sha256",
            "agent_calls",
            "actual_cost_micros",
            "synthetic_cost_micros",
            "started_at",
            "completed_at",
            "limitations",
        }
        if not all(isinstance(key, str) for key in value):
            raise ContractError("maker mark object keys must be strings")
        provided = set(value)
        missing = sorted(expected - provided)
        unknown = sorted(provided - expected)
        if missing or unknown:
            raise ContractError(
                "maker mark fields do not match schema (missing=%s, unknown=%s)"
                % (missing, unknown)
            )
        return cls(**{name: value[name] for name in expected})

    @classmethod
    def from_json(cls, payload: str) -> "MakerMark":
        if not isinstance(payload, str):
            raise ContractError("maker mark JSON must be text")
        if len(payload.encode("utf-8")) > MAX_MAKER_MARK_JSON_BYTES:
            raise ContractError("maker mark JSON exceeds the 262144-byte limit")

        def unique_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ContractError("maker mark JSON contains a duplicate key: %s" % key)
                result[key] = value
            return result

        try:
            value = json.loads(payload, object_pairs_hook=unique_object)
        except json.JSONDecodeError as exc:
            raise ContractError("maker mark JSON is invalid") from exc
        return cls.from_dict(value)
