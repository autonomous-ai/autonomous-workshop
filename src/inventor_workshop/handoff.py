"""Content-bound Manager-to-Inventor process handoff.

The customer CLI launches an inventor as a child process.  This module keeps
that boundary structured: the exact Manager-owned Wish travels over stdin,
while the assignment and routing decision hashes remain attached to the child
result.  No Wish text is interpolated into a shell command.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, TextIO

from .errors import ContractError
from .make import Wish
from .models import require_json_mapping, require_sha256


HANDOFF_KIND = "autonomous-workshop-manager-assignment"
MAX_HANDOFF_BYTES = 1_000_000
RESULT_BINDING_FIELD = "manager_assignment"


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
        raise ContractError("Manager assignment handoff must be JSON-safe") from exc


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _bounded_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    require_json_mapping(value, label)
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # pragma: no cover - canonical JSON
        raise ContractError("%s must be a JSON object" % label) from exc
    if not isinstance(copied, dict):
        raise ContractError("%s must be a JSON object" % label)
    return copied


@dataclass(frozen=True)
class ManagerAssignmentHandoff:
    """The minimum exact assignment identity an Inventor needs to execute."""

    wish: Wish
    inventor_id: str
    playtest_rounds: int
    decision_sha256: str
    assignment_sha256: str
    schema_version: int = 1
    kind: str = HANDOFF_KIND
    wish_sha256: str = field(init=False)
    handoff_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Manager assignment handoff schema_version must be 1")
        if self.kind != HANDOFF_KIND:
            raise ContractError("Manager assignment handoff kind is invalid")
        if not isinstance(self.wish, Wish):
            raise ContractError("Manager assignment handoff requires an exact Wish")
        self.wish.assert_valid()
        _bounded_identifier(self.inventor_id, "Manager assignment inventor_id")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
        ):
            raise ContractError(
                "Manager assignment playtest_rounds must be an integer from 1 to 100"
            )
        require_sha256(self.decision_sha256, "Manager routing decision sha256")
        require_sha256(self.assignment_sha256, "Manager assignment sha256")
        object.__setattr__(self, "wish_sha256", _sha256(self.wish.to_dict()))
        object.__setattr__(self, "handoff_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish": self.wish.to_dict(),
            "wish_sha256": self.wish_sha256,
            "inventor_id": self.inventor_id,
            "playtest_rounds": self.playtest_rounds,
            "decision_sha256": self.decision_sha256,
            "assignment_sha256": self.assignment_sha256,
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["handoff_sha256"] = self.handoff_sha256
        return payload

    def result_binding(self) -> Dict[str, Any]:
        """Return the public identity the child must attach to its result."""

        return {
            "schema_version": 1,
            "product_id": self.wish.product_id,
            "inventor_id": self.inventor_id,
            "wish_sha256": self.wish_sha256,
            "decision_sha256": self.decision_sha256,
            "assignment_sha256": self.assignment_sha256,
            "handoff_sha256": self.handoff_sha256,
        }

    @classmethod
    def from_assignment(cls, assignment: Any) -> "ManagerAssignmentHandoff":
        """Snapshot one validated Manager assignment for a child process."""

        assert_current = getattr(assignment, "assert_current", None)
        if callable(assert_current):
            assert_current()
        try:
            wish = assignment.wish
            inventor_id = assignment.inventor_id
            playtest_rounds = assignment.playtest_rounds
            decision_sha256 = assignment.decision.decision_sha256
            assignment_sha256 = assignment.assignment_sha256
        except AttributeError as exc:
            raise ContractError(
                "Manager assignment handoff requires a complete assignment"
            ) from exc
        return cls(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=playtest_rounds,
            decision_sha256=decision_sha256,
            assignment_sha256=assignment_sha256,
        )

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any], *, expected_inventor_id: str
    ) -> "ManagerAssignmentHandoff":
        payload = _copy_mapping(value, "Manager assignment handoff")
        expected_keys = {
            "schema_version",
            "kind",
            "wish",
            "wish_sha256",
            "inventor_id",
            "playtest_rounds",
            "decision_sha256",
            "assignment_sha256",
            "handoff_sha256",
        }
        if set(payload) != expected_keys:
            raise ContractError("Manager assignment handoff fields are invalid")
        wish_value = payload["wish"]
        if not isinstance(wish_value, Mapping) or set(wish_value) != {
            "schema_version",
            "product_id",
            "objective",
            "constraints",
            "context",
        }:
            raise ContractError("Manager assignment handoff Wish fields are invalid")
        wish = Wish(
            schema_version=wish_value["schema_version"],
            product_id=wish_value["product_id"],
            objective=wish_value["objective"],
            constraints=wish_value["constraints"],
            context=wish_value["context"],
        )
        handoff = cls(
            wish=wish,
            inventor_id=payload["inventor_id"],
            playtest_rounds=payload["playtest_rounds"],
            decision_sha256=payload["decision_sha256"],
            assignment_sha256=payload["assignment_sha256"],
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        _bounded_identifier(expected_inventor_id, "expected inventor_id")
        if handoff.inventor_id != expected_inventor_id:
            raise ContractError("Manager assignment selected a different Inventor")
        if payload["wish_sha256"] != handoff.wish_sha256:
            raise ContractError("Manager assignment Wish identity is inconsistent")
        if payload["handoff_sha256"] != handoff.handoff_sha256:
            raise ContractError("Manager assignment handoff identity is inconsistent")
        return handoff


def read_manager_assignment(
    stream: TextIO, *, expected_inventor_id: str
) -> ManagerAssignmentHandoff:
    """Read one bounded assignment document from stdin."""

    source = stream.read(MAX_HANDOFF_BYTES + 1)
    try:
        encoded_size = len(source.encode("utf-8")) if isinstance(source, str) else 0
    except UnicodeError as exc:
        raise ContractError(
            "Manager assignment handoff must be bounded UTF-8 JSON"
        ) from exc
    if not isinstance(source, str) or not source or encoded_size > MAX_HANDOFF_BYTES:
        raise ContractError("Manager assignment handoff must be bounded UTF-8 JSON")
    try:
        value = json.loads(source)
    except (TypeError, ValueError) as exc:
        raise ContractError("Manager assignment handoff must be valid JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("Manager assignment handoff must be one JSON object")
    return ManagerAssignmentHandoff.from_dict(
        value, expected_inventor_id=expected_inventor_id
    )


def bind_manager_assignment_result(
    result: Mapping[str, Any], handoff: ManagerAssignmentHandoff
) -> Dict[str, Any]:
    """Attach the exact assignment identity to a Workshop child result."""

    if not isinstance(handoff, ManagerAssignmentHandoff):
        raise ContractError("Workshop result binding requires a Manager assignment")
    payload = _copy_mapping(result, "Workshop child result")
    if payload.get("product_id") != handoff.wish.product_id:
        raise ContractError("Workshop child result belongs to a different product")
    if payload.get("playtest_rounds") != handoff.playtest_rounds:
        raise ContractError("Workshop child result changed the assignment Playtest allowance")
    if RESULT_BINDING_FIELD in payload:
        raise ContractError("Workshop child result already contains a Manager assignment")
    payload[RESULT_BINDING_FIELD] = handoff.result_binding()
    return payload


def validate_manager_assignment_result(
    result: Mapping[str, Any], handoff: ManagerAssignmentHandoff
) -> Dict[str, Any]:
    """Validate that returned output is for the exact dispatched assignment."""

    payload = _copy_mapping(result, "Workshop child result")
    binding = payload.get(RESULT_BINDING_FIELD)
    if binding != handoff.result_binding():
        raise ContractError("Workshop child result is not bound to this Manager assignment")
    if payload.get("product_id") != handoff.wish.product_id:
        raise ContractError("Workshop child result belongs to a different product")
    if payload.get("playtest_rounds") != handoff.playtest_rounds:
        raise ContractError("Workshop child result changed the assignment Playtest allowance")
    return payload


__all__ = [
    "HANDOFF_KIND",
    "MAX_HANDOFF_BYTES",
    "RESULT_BINDING_FIELD",
    "ManagerAssignmentHandoff",
    "bind_manager_assignment_result",
    "read_manager_assignment",
    "validate_manager_assignment_result",
]
