"""Deterministic Match contracts for a native-agent product run.

The native agent may rank the materialized personas, but it cannot invent a
persona identity, choose an executable entry point, or turn a model score into
gate authority.  These records bind a Match proposal to the exact immutable
catalog bytes selected by the host.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from workshop._validation import bounded_text, require_sha256
from workshop.errors import ContractError
from workshop.product.blueprints import PLAYTHING_LANES, ToyBlueprint


PERSONA_CATALOG_KIND = "autonomous-workshop.persona-catalog"
MATCH_ASSIGNMENT_KIND = "autonomous-workshop.match-assignment"
MAX_PERSONAS = 256
_PERSONA_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


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


def _persona_id(value: Any, label: str = "persona id") -> str:
    if not isinstance(value, str) or _PERSONA_ID.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase path-safe identifier" % label)
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("%s must be an array" % label)
    return value


@dataclass(frozen=True)
class PersonaCatalogEntry:
    """One host-materialized creative persona available to Match."""

    inventor_id: str
    lane: str
    manifest_sha256: str
    taste_sha256: str

    def __post_init__(self) -> None:
        _persona_id(self.inventor_id, "persona inventor_id")
        if self.lane not in PLAYTHING_LANES:
            raise ContractError("persona lane must be a Workshop plaything lane")
        require_sha256(self.manifest_sha256, "persona manifest sha256")
        require_sha256(self.taste_sha256, "persona TASTE sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "inventor_id": self.inventor_id,
            "lane": self.lane,
            "manifest_sha256": self.manifest_sha256,
            "taste_sha256": self.taste_sha256,
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "PersonaCatalogEntry":
        expected = {"inventor_id", "lane", "manifest_sha256", "taste_sha256"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("persona catalog entry fields are invalid")
        return cls(
            inventor_id=value["inventor_id"],
            lane=value["lane"],
            manifest_sha256=value["manifest_sha256"],
            taste_sha256=value["taste_sha256"],
        )


@dataclass(frozen=True)
class MatchRankingEntry:
    """One stable rank position and Codex rationale, never a model score."""

    inventor_id: str
    rationale: str

    def __post_init__(self) -> None:
        _persona_id(self.inventor_id, "ranked inventor_id")
        bounded_text(self.rationale, "ranked inventor rationale", 2_000)

    def to_dict(self) -> dict[str, str]:
        return {"inventor_id": self.inventor_id, "rationale": self.rationale}

    @classmethod
    def from_mapping(cls, value: Any) -> "MatchRankingEntry":
        if not isinstance(value, Mapping) or set(value) != {"inventor_id", "rationale"}:
            raise ContractError("native Match ranking entry fields are invalid")
        return cls(inventor_id=value["inventor_id"], rationale=value["rationale"])


@dataclass(frozen=True)
class PersonaCatalog:
    """Canonical identity of every persona materialized for one product run."""

    personas: tuple[PersonaCatalogEntry, ...]
    schema_version: int = 1
    kind: str = PERSONA_CATALOG_KIND
    catalog_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("persona catalog schema_version must be 1")
        if self.kind != PERSONA_CATALOG_KIND:
            raise ContractError("persona catalog kind is invalid")
        selected = tuple(self.personas)
        if not 1 <= len(selected) <= MAX_PERSONAS:
            raise ContractError(
                "persona catalog must contain 1 through %d personas" % MAX_PERSONAS
            )
        if not all(isinstance(item, PersonaCatalogEntry) for item in selected):
            raise ContractError("persona catalog entries must be typed personas")
        ordered = tuple(sorted(selected, key=lambda item: item.inventor_id))
        if len({item.inventor_id for item in ordered}) != len(ordered):
            raise ContractError("persona catalog inventor ids must be unique")
        object.__setattr__(self, "personas", ordered)
        object.__setattr__(self, "catalog_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "personas": [item.to_dict() for item in self.personas],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["catalog_sha256"] = self.catalog_sha256
        return payload

    def persona(self, inventor_id: str) -> PersonaCatalogEntry:
        _persona_id(inventor_id, "selected inventor_id")
        for item in self.personas:
            if item.inventor_id == inventor_id:
                return item
        raise ContractError("selected inventor is absent from the immutable catalog")

    @classmethod
    def from_mapping(cls, value: Any) -> "PersonaCatalog":
        expected = {"schema_version", "kind", "personas", "catalog_sha256"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("persona catalog fields are invalid")
        personas = _sequence(value["personas"], "persona catalog personas")
        catalog = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            personas=tuple(PersonaCatalogEntry.from_mapping(item) for item in personas),
        )
        if dict(value) != catalog.to_dict():
            raise ContractError("persona catalog is not canonical or its sha256 is invalid")
        return catalog


@dataclass(frozen=True)
class NativeMatchAssignment:
    """A native Match choice bound to all immutable selection inputs."""

    wish_sha256: str
    persona_catalog_sha256: str
    selected_inventor_id: str
    selected_lane: str
    selected_manifest_sha256: str
    selected_taste_sha256: str
    blueprint_sha256: str
    ranking: tuple[MatchRankingEntry, ...]
    schema_version: int = 1
    kind: str = MATCH_ASSIGNMENT_KIND
    assignment_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native Match assignment schema_version must be 1")
        if self.kind != MATCH_ASSIGNMENT_KIND:
            raise ContractError("native Match assignment kind is invalid")
        require_sha256(self.wish_sha256, "native Match Wish sha256")
        require_sha256(
            self.persona_catalog_sha256, "native Match persona catalog sha256"
        )
        _persona_id(self.selected_inventor_id, "selected inventor_id")
        if self.selected_lane not in PLAYTHING_LANES:
            raise ContractError("selected lane must be a Workshop plaything lane")
        require_sha256(self.selected_manifest_sha256, "selected manifest sha256")
        require_sha256(self.selected_taste_sha256, "selected TASTE sha256")
        require_sha256(self.blueprint_sha256, "selected blueprint sha256")
        expected_blueprint = ToyBlueprint.for_lane(self.selected_lane).sha256
        if self.blueprint_sha256 != expected_blueprint:
            raise ContractError("blueprint sha256 is not derived from the selected lane")

        ranking = tuple(self.ranking)
        if not 1 <= len(ranking) <= MAX_PERSONAS:
            raise ContractError(
                "native Match ranking must contain 1 through %d entries"
                % MAX_PERSONAS
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
            "persona_catalog_sha256": self.persona_catalog_sha256,
            "selected_inventor_id": self.selected_inventor_id,
            "selected_lane": self.selected_lane,
            "selected_manifest_sha256": self.selected_manifest_sha256,
            "selected_taste_sha256": self.selected_taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "ranking": [item.to_dict() for item in self.ranking],
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["assignment_sha256"] = self.assignment_sha256
        return payload

    def assert_context(self, *, wish_sha256: str, catalog: PersonaCatalog) -> None:
        """Reject selection details not derived from the exact host catalog."""

        require_sha256(wish_sha256, "expected native Match Wish sha256")
        if not isinstance(catalog, PersonaCatalog):
            raise ContractError("native Match context requires a PersonaCatalog")
        if self.wish_sha256 != wish_sha256:
            raise ContractError("native Match assignment belongs to another Wish")
        if self.persona_catalog_sha256 != catalog.catalog_sha256:
            raise ContractError("native Match assignment belongs to another persona catalog")
        expected_ids = tuple(item.inventor_id for item in catalog.personas)
        if set(self.ranked_inventor_ids) != set(expected_ids) or len(
            self.ranked_inventor_ids
        ) != len(expected_ids):
            raise ContractError(
                "native Match ranking must cover every catalog persona exactly once"
            )
        selected = catalog.persona(self.selected_inventor_id)
        if (
            self.selected_lane != selected.lane
            or self.selected_manifest_sha256 != selected.manifest_sha256
            or self.selected_taste_sha256 != selected.taste_sha256
        ):
            raise ContractError("native Match selection differs from the immutable persona")

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeMatchAssignment":
        expected = {
            "schema_version",
            "kind",
            "wish_sha256",
            "persona_catalog_sha256",
            "selected_inventor_id",
            "selected_lane",
            "selected_manifest_sha256",
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
            persona_catalog_sha256=value["persona_catalog_sha256"],
            selected_inventor_id=value["selected_inventor_id"],
            selected_lane=value["selected_lane"],
            selected_manifest_sha256=value["selected_manifest_sha256"],
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
    "MAX_PERSONAS",
    "MatchRankingEntry",
    "NativeMatchAssignment",
    "PERSONA_CATALOG_KIND",
    "PersonaCatalog",
    "PersonaCatalogEntry",
]
