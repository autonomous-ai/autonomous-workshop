"""Deterministic Invent contract for the native-agent runtime.

Invent remains cognitive work owned by the native agent.  This module only
identifies the exact Wish, Match assignment, creative persona, lane blueprint,
concept, and research bytes that the host is being asked to accept.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.errors import ContractError
from workshop.match.native import NativeMatchAssignment
from workshop.product.blueprints import PLAYTHING_LANES


INVENTED_V2_KIND = "autonomous-workshop.invented"
MAX_INVENTED_V2_BYTES = 2 * 1024 * 1024


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Invented v2 values must be finite JSON") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class InventedV2:
    """One concept proposal with content-addressed research and no self-score."""

    wish_sha256: str
    assignment_sha256: str
    taste_sha256: str
    blueprint_sha256: str
    lane: str
    concept: Mapping[str, Any]
    research: Mapping[str, Any]
    schema_version: int = 2
    kind: str = INVENTED_V2_KIND
    concept_sha256: str = field(init=False)
    research_sha256: str = field(init=False)
    invented_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 2:
            raise ContractError("Invented v2 schema_version must be 2")
        if self.kind != INVENTED_V2_KIND:
            raise ContractError("Invented v2 kind is invalid")
        require_sha256(self.wish_sha256, "Invented v2 Wish sha256")
        require_sha256(self.assignment_sha256, "Invented v2 assignment sha256")
        require_sha256(self.taste_sha256, "Invented v2 TASTE sha256")
        require_sha256(self.blueprint_sha256, "Invented v2 blueprint sha256")
        if self.lane not in PLAYTHING_LANES:
            raise ContractError("Invented v2 lane must be a Workshop plaything lane")

        concept = copy_json_mapping(self.concept, "Invented v2 concept", nonempty=True)
        research = copy_json_mapping(
            self.research, "Invented v2 research", nonempty=True
        )
        for key in ("title", "summary"):
            bounded_text(concept.get(key), "Invented v2 concept %s" % key, 2_000)
        frozen_concept = _freeze(concept)
        frozen_research = _freeze(research)
        object.__setattr__(self, "concept", frozen_concept)
        object.__setattr__(self, "research", frozen_research)
        object.__setattr__(self, "concept_sha256", _sha256(concept))
        object.__setattr__(self, "research_sha256", _sha256(research))
        identity = self._identity_dict()
        bounded_payload = {**identity, "invented_sha256": "0" * 64}
        if len(_canonical_json(bounded_payload)) > MAX_INVENTED_V2_BYTES:
            raise ContractError("Invented v2 exceeds its byte limit")
        object.__setattr__(self, "invented_sha256", _sha256(identity))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish_sha256": self.wish_sha256,
            "assignment_sha256": self.assignment_sha256,
            "taste_sha256": self.taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "lane": self.lane,
            "concept": _thaw(self.concept),
            "concept_sha256": self.concept_sha256,
            "research": _thaw(self.research),
            "research_sha256": self.research_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["invented_sha256"] = self.invented_sha256
        return payload

    def assert_context(self, assignment: NativeMatchAssignment) -> None:
        """Reject a concept detached from the exact accepted Match choice."""

        if not isinstance(assignment, NativeMatchAssignment):
            raise ContractError("Invented v2 context requires a native Match assignment")
        if (
            self.wish_sha256 != assignment.wish_sha256
            or self.assignment_sha256 != assignment.assignment_sha256
            or self.taste_sha256 != assignment.selected_taste_sha256
            or self.blueprint_sha256 != assignment.blueprint_sha256
            or self.lane != assignment.selected_lane
        ):
            raise ContractError("Invented v2 belongs to different Workshop inputs")

    @classmethod
    def from_mapping(cls, value: Any) -> "InventedV2":
        expected = {
            "schema_version",
            "kind",
            "wish_sha256",
            "assignment_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "lane",
            "concept",
            "concept_sha256",
            "research",
            "research_sha256",
            "invented_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("Invented v2 fields are invalid")
        invented = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            wish_sha256=value["wish_sha256"],
            assignment_sha256=value["assignment_sha256"],
            taste_sha256=value["taste_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            lane=value["lane"],
            concept=value["concept"],
            research=value["research"],
        )
        if dict(value) != invented.to_dict():
            raise ContractError("Invented v2 content hashes or canonical sha256 are invalid")
        return invented


__all__ = ["INVENTED_V2_KIND", "MAX_INVENTED_V2_BYTES", "InventedV2"]
