"""Deterministic Invent contract for the native-agent runtime.

Invent remains cognitive work owned by the native agent.  This module only
identifies the exact Wish, Match assignment, selected Inventor, open-ended
validation baseline, concept, and research bytes the host is asked to accept.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.errors import ContractError
from workshop.match.native import NativeMatchAssignment


INVENTED_KIND = "autonomous-workshop.invented"
MAX_INVENTED_BYTES = 2 * 1024 * 1024
# Schema 3 bound only `title` and `summary`; schema 4 adds the concept
# contract below.  Both stay readable so sealed runs keep resuming; the
# run-local finalizer emits schema 4 only.
INVENTED_SCHEMA_VERSIONS = (3, 4, 5)
BUILD_GROUP_FIELDS = frozenset(("group", "parts", "exit_criteria"))
MAX_BUILD_GROUPS = 16
CONCEPT_CONTRACT_FIELDS = frozenset(
    ("title", "summary", "interaction", "envelope_mm", "mechanisms", "components")
)
COMPONENT_CONTRACT_FIELDS = frozenset(
    (
        "key",
        "name",
        "form",
        "duty",
        "dimensions_mm",
        "placement",
        "interfaces",
        "mates_with",
        "signature",
    )
)
DIMENSION_KEYS = ("length_mm", "width_mm", "height_mm")
HEDGED_COMPONENT_FIELDS = ("form", "duty", "placement", "interfaces")
MAX_CONCEPT_COMPONENTS = 64
MAX_CONCEPT_MECHANISMS = 16
MAX_DIMENSION_MM = 2000.0
CONCEPT_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
# A physical description that hedges a quantity is a wish, not a contract.
NUMERIC_HEDGE_RE = re.compile(
    r"(?i)\b(?:roughly|about|approximately|around|circa)\s+\d|~\s*\d"
)
QUANTITY_HEDGE_RE = re.compile(
    r"(?i)\b(?:some|several|a few|a number of|a couple of|multiple|various|"
    r"enough|as needed|or so)\b"
)


def _dimensions_mm(value: Any, label: str) -> list[float]:
    if not isinstance(value, Mapping) or set(value) != set(DIMENSION_KEYS):
        raise ContractError(
            "%s must contain exactly length_mm, width_mm, and height_mm" % label
        )
    result: list[float] = []
    for key in DIMENSION_KEYS:
        item = value[key]
        if (
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            or not 0 < item <= MAX_DIMENSION_MM
        ):
            raise ContractError(
                "%s %s must be a finite millimetre value within (0, %d]"
                % (label, key, int(MAX_DIMENSION_MM))
            )
        result.append(float(item))
    return result


def _hedged(text: str) -> Optional[str]:
    match = NUMERIC_HEDGE_RE.search(text) or QUANTITY_HEDGE_RE.search(text)
    return match.group(0) if match else None


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ContractError(
            "%s must be a %slist" % (label, "non-empty " if nonempty else "")
        )
    return list(value)


def _exact_fields(value: Any, expected: frozenset, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ContractError("%s fields are invalid" % label)
    return dict(value)


def validate_concept_contract(concept: Mapping[str, Any]) -> None:
    """Host mirror of the run-local Invent concept contract (schema 4).

    The finalizer applies the same rules where the agent can act on them; the
    host re-applies them so a hand-written invented.json cannot bypass them.
    """

    missing = sorted(CONCEPT_CONTRACT_FIELDS - set(concept))
    if missing:
        raise ContractError(
            "Invented concept lacks required contract fields: %s" % ", ".join(missing)
        )
    bounded_text(concept["title"], "Invented concept title", 2_000)
    bounded_text(concept["summary"], "Invented concept summary", 2_000)
    interaction = bounded_text(
        concept["interaction"], "Invented concept interaction", 4_000
    ).casefold()
    envelope = sorted(_dimensions_mm(concept["envelope_mm"], "Invented concept envelope_mm"))
    mechanisms = _list(concept["mechanisms"], "Invented concept mechanisms")
    if (
        len(mechanisms) > MAX_CONCEPT_MECHANISMS
        or any(
            not isinstance(item, str) or CONCEPT_SLUG_RE.fullmatch(item) is None
            for item in mechanisms
        )
        or len(set(mechanisms)) != len(mechanisms)
    ):
        raise ContractError(
            "Invented concept mechanisms must be at most %d unique slugs"
            % MAX_CONCEPT_MECHANISMS
        )
    components = _list(concept["components"], "Invented concept components", nonempty=True)
    if len(components) > MAX_CONCEPT_COMPONENTS:
        raise ContractError(
            "Invented concept components exceed %d entries" % MAX_CONCEPT_COMPONENTS
        )
    parsed: dict[str, dict[str, Any]] = {}
    for raw in components:
        item = _exact_fields(raw, COMPONENT_CONTRACT_FIELDS, "Invented component")
        key = item["key"]
        if (
            not isinstance(key, str)
            or CONCEPT_SLUG_RE.fullmatch(key) is None
            or key in parsed
        ):
            raise ContractError("Invented component key must be a unique slug")
        name = bounded_text(item["name"], "Invented component %s name" % key, 200)
        for field_name in HEDGED_COMPONENT_FIELDS:
            text = bounded_text(
                item[field_name], "Invented component %s %s" % (key, field_name), 4_000
            )
            hedge = _hedged(text)
            if hedge is not None:
                raise ContractError(
                    "Invented component %s %s uses an unbound quantity %r; "
                    "state the number (unbound)" % (key, field_name, hedge)
                )
        dims = sorted(
            _dimensions_mm(item["dimensions_mm"], "Invented component %s dimensions_mm" % key)
        )
        if any(dim > limit for dim, limit in zip(dims, envelope)):
            raise ContractError(
                "Invented component %s exceeds the concept envelope (envelope)" % key
            )
        if type(item["signature"]) is not bool:
            raise ContractError("Invented component %s signature must be boolean" % key)
        mates = _list(item["mates_with"], "Invented component %s mates_with" % key)
        parsed[key] = {"name": name, "mates": mates, "signature": item["signature"]}
    for key, component in parsed.items():
        mates = component["mates"]
        if len(set(mates)) != len(mates) or any(
            not isinstance(mate, str) or mate == key or mate not in parsed
            for mate in mates
        ):
            raise ContractError(
                "Invented component %s mates_with must name other existing "
                "components exactly once (component-orphan)" % key
            )
    signatures = [key for key, component in parsed.items() if component["signature"]]
    if len(signatures) != 1:
        raise ContractError(
            "Invented concept must flag exactly one signature component, found %d "
            "(signature)" % len(signatures)
        )
    mated: set[str] = set()
    for key, component in parsed.items():
        if component["mates"]:
            mated.add(key)
            mated.update(component["mates"])
    for key, component in parsed.items():
        spoken = (key, key.replace("_", " ").replace("-", " "), component["name"].casefold())
        if key not in mated and not any(term in interaction for term in spoken):
            raise ContractError(
                "Invented component %s is decoration: nothing mates with it and "
                "the interaction never uses it (decoration)" % key
            )



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
        raise ContractError("Invented values must be finite JSON") from exc


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


def validate_build_plan(concept: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Host mirror of the schema-5 build plan: a complete partition of components.

    Every component sits in exactly one group, in the author's build order, so
    Make can seal one bounded group at a time and stop when one fails instead
    of building on it.
    """

    plan = _list(concept.get("build_plan"), "Invented concept build_plan", nonempty=True)
    if len(plan) > MAX_BUILD_GROUPS:
        raise ContractError("Invented concept build_plan exceeds %d groups" % MAX_BUILD_GROUPS)
    components = {item["key"]: item for item in concept["components"]}
    placed: dict[str, int] = {}
    groups: list[dict[str, Any]] = []
    for index, raw in enumerate(plan):
        group = _exact_fields(raw, BUILD_GROUP_FIELDS, "Invented build group")
        name = group["group"]
        if (
            not isinstance(name, str)
            or CONCEPT_SLUG_RE.fullmatch(name) is None
            or any(item["group"] == name for item in groups)
        ):
            raise ContractError("Invented build group name must be a unique slug")
        bounded_text(group["exit_criteria"], "Invented build group %s exit_criteria" % name, 2_000)
        parts = _list(group["parts"], "Invented build group %s parts" % name, nonempty=True)
        for part in parts:
            if not isinstance(part, str) or part not in components:
                raise ContractError(
                    "Invented build group %s names an unknown component %r (build-plan)"
                    % (name, part)
                )
            if part in placed:
                raise ContractError(
                    "Invented component %s is placed in more than one build group (build-plan)"
                    % part
                )
            placed[part] = index
        groups.append({"group": name, "parts": list(parts), "exit_criteria": group["exit_criteria"]})
    missing = sorted(set(components) - set(placed))
    if missing:
        raise ContractError(
            "Invented build_plan leaves components unplaced: %s (build-plan)" % ", ".join(missing)
        )
    return groups



@dataclass(frozen=True)
class NativeInvented:
    """One concept proposal with content-addressed research and no self-score."""

    wish_sha256: str
    assignment_sha256: str
    taste_sha256: str
    blueprint_sha256: str
    concept: Mapping[str, Any]
    research: Mapping[str, Any]
    schema_version: int = 3
    kind: str = INVENTED_KIND
    concept_sha256: str = field(init=False)
    research_sha256: str = field(init=False)
    invented_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version not in INVENTED_SCHEMA_VERSIONS
        ):
            raise ContractError("Invented contract schema_version must be 3, 4, or 5")
        if self.kind != INVENTED_KIND:
            raise ContractError("Invented kind is invalid")
        require_sha256(self.wish_sha256, "Invented Wish sha256")
        require_sha256(self.assignment_sha256, "Invented assignment sha256")
        require_sha256(self.taste_sha256, "Invented TASTE sha256")
        require_sha256(self.blueprint_sha256, "Invented blueprint sha256")
        concept = copy_json_mapping(self.concept, "Invented concept", nonempty=True)
        research = copy_json_mapping(
            self.research, "Invented research", nonempty=True
        )
        if self.schema_version >= 4:
            validate_concept_contract(concept)
            if self.schema_version >= 5:
                validate_build_plan(concept)
        else:
            for key in ("title", "summary"):
                bounded_text(concept.get(key), "Invented concept %s" % key, 2_000)
        frozen_concept = _freeze(concept)
        frozen_research = _freeze(research)
        object.__setattr__(self, "concept", frozen_concept)
        object.__setattr__(self, "research", frozen_research)
        object.__setattr__(self, "concept_sha256", _sha256(concept))
        object.__setattr__(self, "research_sha256", _sha256(research))
        identity = self._identity_dict()
        bounded_payload = {**identity, "invented_sha256": "0" * 64}
        if len(_canonical_json(bounded_payload)) > MAX_INVENTED_BYTES:
            raise ContractError("Invented exceeds its byte limit")
        object.__setattr__(self, "invented_sha256", _sha256(identity))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish_sha256": self.wish_sha256,
            "assignment_sha256": self.assignment_sha256,
            "taste_sha256": self.taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
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
            raise ContractError("Invented context requires a native Match assignment")
        if (
            self.wish_sha256 != assignment.wish_sha256
            or self.assignment_sha256 != assignment.assignment_sha256
            or self.taste_sha256 != assignment.selected_taste_sha256
            or self.blueprint_sha256 != assignment.blueprint_sha256
        ):
            raise ContractError("Invented belongs to different Workshop inputs")

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeInvented":
        expected = {
            "schema_version",
            "kind",
            "wish_sha256",
            "assignment_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "concept",
            "concept_sha256",
            "research",
            "research_sha256",
            "invented_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("Invented fields are invalid")
        invented = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            wish_sha256=value["wish_sha256"],
            assignment_sha256=value["assignment_sha256"],
            taste_sha256=value["taste_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            concept=value["concept"],
            research=value["research"],
        )
        if dict(value) != invented.to_dict():
            raise ContractError("Invented content hashes or canonical sha256 are invalid")
        return invented


__all__ = [
    "INVENTED_KIND",
    "INVENTED_SCHEMA_VERSIONS",
    "MAX_INVENTED_BYTES",
    "NativeInvented",
    "validate_build_plan",
    "validate_concept_contract",
]
