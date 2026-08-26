"""Deterministic Match contracts for a native-agent product run.

The native agent may rank the materialized Inventors, but it cannot invent an
Inventor identity, choose an executable entry point, or turn a model score into
gate authority.  These records bind a Match proposal to the exact immutable
roster bytes selected by the host.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from workshop._validation import bounded_text, require_sha256
from workshop.errors import ContractError
from workshop.product.blueprints import ToyBlueprint
from workshop.runtime.managers import SUPPORTED_MANAGER_IDS, manager_spec


INVENTOR_ROSTER_KIND = "autonomous-workshop.inventor-roster"
MATCH_ASSIGNMENT_KIND = "autonomous-workshop.match-assignment"
MAX_INVENTORS = 256
_INVENTOR_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


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
        raise ContractError("native Match values must be finite JSON") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _inventor_id(value: Any, label: str = "inventor id") -> str:
    if not isinstance(value, str) or _INVENTOR_ID.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase path-safe identifier" % label)
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("%s must be an array" % label)
    return value


def _valid_agent_paths(inventor_id: str) -> frozenset[str]:
    return frozenset(
        manager_spec(manager_id).agent_path(inventor_id)
        for manager_id in SUPPORTED_MANAGER_IDS
    )


@dataclass(frozen=True)
class InventorRosterEntry:
    """One exact project-scoped custom agent available to Match."""

    inventor_id: str
    agent_path: str
    agent_sha256: str
    source_manifest_sha256: str
    taste_sha256: str

    def __post_init__(self) -> None:
        _inventor_id(self.inventor_id, "Inventor id")
        if self.agent_path not in _valid_agent_paths(self.inventor_id):
            raise ContractError(
                "Inventor agent path must use a supported Manager convention"
            )
        require_sha256(self.agent_sha256, "Inventor custom-agent sha256")
        require_sha256(
            self.source_manifest_sha256, "Inventor source manifest sha256"
        )
        require_sha256(self.taste_sha256, "Inventor TASTE sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "inventor_id": self.inventor_id,
            "agent_path": self.agent_path,
            "agent_sha256": self.agent_sha256,
            "source_manifest_sha256": self.source_manifest_sha256,
            "taste_sha256": self.taste_sha256,
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "InventorRosterEntry":
        expected = {
            "inventor_id",
            "agent_path",
            "agent_sha256",
            "source_manifest_sha256",
            "taste_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("inventor roster entry fields are invalid")
        return cls(
            inventor_id=value["inventor_id"],
            agent_path=value["agent_path"],
            agent_sha256=value["agent_sha256"],
            source_manifest_sha256=value["source_manifest_sha256"],
            taste_sha256=value["taste_sha256"],
        )


@dataclass(frozen=True)
class MatchRankingEntry:
    """One stable rank position and Manager rationale, never a model score."""

    inventor_id: str
    rationale: str

    def __post_init__(self) -> None:
        _inventor_id(self.inventor_id, "ranked inventor_id")
        bounded_text(self.rationale, "ranked inventor rationale", 2_000)

    def to_dict(self) -> dict[str, str]:
        return {"inventor_id": self.inventor_id, "rationale": self.rationale}

    @classmethod
    def from_mapping(cls, value: Any) -> "MatchRankingEntry":
        if not isinstance(value, Mapping) or set(value) != {"inventor_id", "rationale"}:
            raise ContractError("native Match ranking entry fields are invalid")
        return cls(inventor_id=value["inventor_id"], rationale=value["rationale"])


@dataclass(frozen=True)
class InventorRoster:
    """Canonical identity of every inventor materialized for one product run."""

    inventors: tuple[InventorRosterEntry, ...]
    schema_version: int = 1
    kind: str = INVENTOR_ROSTER_KIND
    roster_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Inventor roster schema_version must be 1")
        if self.kind != INVENTOR_ROSTER_KIND:
            raise ContractError("inventor roster kind is invalid")
        selected = tuple(self.inventors)
        if not 1 <= len(selected) <= MAX_INVENTORS:
            raise ContractError(
                "inventor roster must contain 1 through %d inventors" % MAX_INVENTORS
            )
        if not all(isinstance(item, InventorRosterEntry) for item in selected):
            raise ContractError("inventor roster entries must be typed inventors")
        ordered = tuple(sorted(selected, key=lambda item: item.inventor_id))
        if len({item.inventor_id for item in ordered}) != len(ordered):
            raise ContractError("inventor roster inventor ids must be unique")
        object.__setattr__(self, "inventors", ordered)
        object.__setattr__(self, "roster_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "inventors": [item.to_dict() for item in self.inventors],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["roster_sha256"] = self.roster_sha256
        return payload

    def inventor(self, inventor_id: str) -> InventorRosterEntry:
        _inventor_id(inventor_id, "selected inventor_id")
        for item in self.inventors:
            if item.inventor_id == inventor_id:
                return item
        raise ContractError("selected inventor is absent from the immutable roster")

    @classmethod
    def from_mapping(cls, value: Any) -> "InventorRoster":
        expected = {"schema_version", "kind", "inventors", "roster_sha256"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("inventor roster fields are invalid")
        inventors = _sequence(value["inventors"], "inventor roster inventors")
        roster = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            inventors=tuple(InventorRosterEntry.from_mapping(item) for item in inventors),
        )
        if dict(value) != roster.to_dict():
            raise ContractError("inventor roster is not canonical or its sha256 is invalid")
        return roster


@dataclass(frozen=True)
class NativeMatchAssignment:
    """A native Match choice bound to all immutable selection inputs."""

    wish_sha256: str
    inventor_roster_sha256: str
    selected_inventor_id: str
    selected_agent_path: str
    selected_agent_sha256: str
    selected_source_manifest_sha256: str
    selected_taste_sha256: str
    blueprint_sha256: str
    ranking: tuple[MatchRankingEntry, ...]
    schema_version: int = 3
    kind: str = MATCH_ASSIGNMENT_KIND
    assignment_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 3:
            raise ContractError("native Match assignment schema_version must be 3")
        if self.kind != MATCH_ASSIGNMENT_KIND:
            raise ContractError("native Match assignment kind is invalid")
        require_sha256(self.wish_sha256, "native Match Wish sha256")
        require_sha256(
            self.inventor_roster_sha256, "native Match inventor roster sha256"
        )
        _inventor_id(self.selected_inventor_id, "selected inventor_id")
        if self.selected_agent_path not in _valid_agent_paths(
            self.selected_inventor_id
        ):
            raise ContractError("selected custom-agent path differs from its Inventor")
        require_sha256(self.selected_agent_sha256, "selected custom-agent sha256")
        require_sha256(
            self.selected_source_manifest_sha256,
            "selected source manifest sha256",
        )
        require_sha256(self.selected_taste_sha256, "selected TASTE sha256")
        require_sha256(self.blueprint_sha256, "selected blueprint sha256")
        expected_blueprint = ToyBlueprint().sha256
        if self.blueprint_sha256 != expected_blueprint:
            raise ContractError("blueprint sha256 is not the open-ended Workshop baseline")

        ranking = tuple(self.ranking)
        if not 1 <= len(ranking) <= MAX_INVENTORS:
            raise ContractError(
                "native Match ranking must contain 1 through %d entries"
                % MAX_INVENTORS
            )
        if not all(isinstance(item, MatchRankingEntry) for item in ranking):
            raise ContractError("native Match ranking entries must be typed values")
        ranked_ids = tuple(item.inventor_id for item in ranking)
        if len(set(ranked_ids)) != len(ranked_ids):
            raise ContractError("native Match ranking inventor ids must be unique")
        if ranked_ids[0] != self.selected_inventor_id:
            raise ContractError("selected inventor must be first in the stable ranking")
        object.__setattr__(self, "ranking", ranking)
        object.__setattr__(self, "assignment_sha256", _sha256(self._identity_dict()))

    @property
    def ranked_inventor_ids(self) -> tuple[str, ...]:
        return tuple(item.inventor_id for item in self.ranking)

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish_sha256": self.wish_sha256,
            "inventor_roster_sha256": self.inventor_roster_sha256,
            "selected_inventor_id": self.selected_inventor_id,
            "selected_agent_path": self.selected_agent_path,
            "selected_agent_sha256": self.selected_agent_sha256,
            "selected_source_manifest_sha256": self.selected_source_manifest_sha256,
            "selected_taste_sha256": self.selected_taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "ranking": [item.to_dict() for item in self.ranking],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["assignment_sha256"] = self.assignment_sha256
        return payload

    def assert_context(self, *, wish_sha256: str, roster: InventorRoster) -> None:
        """Reject selection details not derived from the exact host roster."""

        require_sha256(wish_sha256, "expected native Match Wish sha256")
        if not isinstance(roster, InventorRoster):
            raise ContractError("native Match context requires an InventorRoster")
        if self.wish_sha256 != wish_sha256:
            raise ContractError("native Match assignment belongs to another Wish")
        if self.inventor_roster_sha256 != roster.roster_sha256:
            raise ContractError("native Match assignment belongs to another inventor roster")
        expected_ids = tuple(item.inventor_id for item in roster.inventors)
        if set(self.ranked_inventor_ids) != set(expected_ids) or len(
            self.ranked_inventor_ids
        ) != len(expected_ids):
            raise ContractError(
                "native Match ranking must cover every roster inventor exactly once"
            )
        selected = roster.inventor(self.selected_inventor_id)
        if (
            self.selected_agent_path != selected.agent_path
            or self.selected_agent_sha256 != selected.agent_sha256
            or self.selected_source_manifest_sha256
            != selected.source_manifest_sha256
            or self.selected_taste_sha256 != selected.taste_sha256
        ):
            raise ContractError("native Match selection differs from the immutable inventor")

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeMatchAssignment":
        expected = {
            "schema_version",
            "kind",
            "wish_sha256",
            "inventor_roster_sha256",
            "selected_inventor_id",
            "selected_agent_path",
            "selected_agent_sha256",
            "selected_source_manifest_sha256",
            "selected_taste_sha256",
            "blueprint_sha256",
            "ranking",
            "assignment_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Match assignment fields are invalid")
        ranking = _sequence(value["ranking"], "native Match ranking")
        assignment = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            wish_sha256=value["wish_sha256"],
            inventor_roster_sha256=value["inventor_roster_sha256"],
            selected_inventor_id=value["selected_inventor_id"],
            selected_agent_path=value["selected_agent_path"],
            selected_agent_sha256=value["selected_agent_sha256"],
            selected_source_manifest_sha256=value[
                "selected_source_manifest_sha256"
            ],
            selected_taste_sha256=value["selected_taste_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            ranking=tuple(MatchRankingEntry.from_mapping(item) for item in ranking),
        )
        if dict(value) != assignment.to_dict():
            raise ContractError(
                "native Match assignment is not canonical or its sha256 is invalid"
            )
        return assignment


__all__ = [
    "MATCH_ASSIGNMENT_KIND",
    "MAX_INVENTORS",
    "MatchRankingEntry",
    "NativeMatchAssignment",
    "INVENTOR_ROSTER_KIND",
    "InventorRoster",
    "InventorRosterEntry",
]
