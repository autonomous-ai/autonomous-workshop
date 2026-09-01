"""Simplified two-input Concept authoring and normalized Concept v3 contracts.

The native Manager owns the two inputs validated here.  Everything returned by
``normalize_authored_concept`` is a copy, lossless projection, canonical path,
or content identity; this module deliberately contains no defaults or design
selection.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import NativeMatchAssignment
from workshop.wish import Wish

from .v2 import SealedConcept


VISUAL_PLAN_KIND = "autonomous-workshop.concept-visual-plan"
PRE_RENDER_CONCEPT_V3_KIND = "autonomous-workshop.concept-pre-render"
SEALED_CONCEPT_V3_KIND = "autonomous-workshop.concept-sealed"
MAX_VISUAL_ROLES = 20
ROLE_KINDS = frozenset(
    ("primary-form", "signature-experience", "assembly", "alternate-view", "component")
)
_ID_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("simplified Concept values must be finite JSON") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


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


def _object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError("%s fields are invalid" % label)
    return dict(value)


def _array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("%s must be an array" % label)
    result = list(value)
    if nonempty and not result:
        raise ContractError("%s must not be empty" % label)
    return result


def _text(value: Any, label: str, maximum: int = 8_000) -> str:
    return bounded_text(value, label, maximum)


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ContractError("%s must be a safe lowercase identifier" % label)
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 100_000:
        raise ContractError("%s must be a positive bounded number" % label)
    return float(value)


def _validate_measurements(value: Any, label: str) -> dict[str, Any]:
    result = _object(value, {"description", "values_mm"}, label)
    _text(result["description"], "%s description" % label, 2_000)
    values = copy_json_mapping(result["values_mm"], "%s values_mm" % label, nonempty=True)
    for key, number in values.items():
        _identifier(key, "%s measurement key" % label)
        _number(number, "%s.%s" % (label, key))
    result["values_mm"] = dict(values)
    return result


def validate_authored_source(value: Any) -> dict[str, Any]:
    """Validate and return the strict consolidated v2 Invent source."""

    source = _object(
        value,
        {"selected_inventor_id", "ranking", "concept", "research"},
        "simplified Invent source",
    )
    _identifier(source["selected_inventor_id"], "selected inventor id")
    ranking = _array(source["ranking"], "Invent ranking", nonempty=True)
    ranked: list[str] = []
    for item in ranking:
        entry = _object(item, {"inventor_id", "rationale"}, "Invent ranking entry")
        ranked.append(_identifier(entry["inventor_id"], "ranked inventor id"))
        _text(entry["rationale"], "ranking rationale", 4_000)
    if len(ranked) != len(set(ranked)) or ranked[0] != source["selected_inventor_id"]:
        raise ContractError("Invent ranking must be unique and place the selection first")

    concept_fields = {
        "title", "summary", "object", "category", "signature_interaction",
        "anti_generic_signature", "intended_experience", "non_negotiable_constraints",
        "envelope_mm", "print_stance", "components", "interaction_trace",
        "make_proof_target", "constraints", "decisions", "assumptions", "unresolved_risks",
    }
    concept = _object(source["concept"], concept_fields, "simplified physical concept")
    for name in (
        "title", "summary", "object", "category", "signature_interaction",
        "anti_generic_signature", "intended_experience",
    ):
        _text(concept[name], "concept %s" % name, 4_000)
    for name in ("non_negotiable_constraints", "assumptions", "unresolved_risks"):
        for index, item in enumerate(_array(concept[name], "concept %s" % name)):
            _text(item, "concept %s %d" % (name, index), 2_000)
    envelope = copy_json_mapping(concept["envelope_mm"], "concept envelope_mm", nonempty=True)
    for key, number in envelope.items():
        _identifier(key, "concept envelope dimension")
        _number(number, "concept envelope_mm.%s" % key)
    print_stance = _object(
        concept["print_stance"], {"orientation", "supports_required", "support_notes"},
        "concept print stance",
    )
    _text(print_stance["orientation"], "concept print orientation", 2_000)
    if type(print_stance["supports_required"]) is not bool:
        raise ContractError("concept supports_required must be boolean")
    if not isinstance(print_stance["support_notes"], str) or len(print_stance["support_notes"]) > 2_000:
        raise ContractError("concept support_notes must be bounded text")

    components = _array(concept["components"], "concept components", nonempty=True)
    component_keys: list[str] = []
    component_fields = {
        "key", "name", "purpose", "form", "measurements", "placement", "interfaces",
        "assembly_relationship", "signature_contribution",
    }
    for raw in components:
        component = _object(raw, component_fields, "concept component")
        key = _identifier(component["key"], "concept component key")
        component_keys.append(key)
        for name in component_fields - {"key", "measurements"}:
            _text(component[name], "component %s %s" % (key, name), 3_000)
        _validate_measurements(component["measurements"], "component %s measurements" % key)
    if len(component_keys) != len(set(component_keys)):
        raise ContractError("concept component keys must be unique")

    trace = _array(concept["interaction_trace"], "concept interaction trace", nonempty=True)
    for index, raw in enumerate(trace):
        step = _object(raw, {"step", "component_keys", "cause", "effect"}, "interaction trace step")
        if type(step["step"]) is not int or step["step"] != index + 1:
            raise ContractError("interaction trace steps must be consecutive from one")
        keys = _array(step["component_keys"], "interaction trace component_keys", nonempty=True)
        if len(keys) != len(set(keys)) or any(key not in component_keys for key in keys):
            raise ContractError("interaction trace names unknown or duplicate components")
        _text(step["cause"], "interaction trace cause", 3_000)
        _text(step["effect"], "interaction trace effect", 3_000)

    proof = _object(
        concept["make_proof_target"],
        {"claim", "method", "success_condition", "failure_condition"},
        "Make proof target",
    )
    for name, item in proof.items():
        _text(item, "Make proof target %s" % name, 4_000)

    decisions = _array(concept["decisions"], "concept decisions")
    decision_ids: set[str] = set()
    for raw in decisions:
        decision = _object(raw, {"id", "decision", "reason"}, "concept decision")
        decision_id = _identifier(decision["id"], "concept decision id")
        if decision_id in decision_ids:
            raise ContractError("concept decision ids must be unique")
        decision_ids.add(decision_id)
        _text(decision["decision"], "concept decision", 4_000)
        _text(decision["reason"], "concept decision reason", 4_000)

    research = _object(source["research"], {"sources", "findings"}, "Invent research")
    sources = _array(research["sources"], "research sources")
    findings = _array(research["findings"], "research findings")
    if bool(sources) != bool(findings):
        raise ContractError("research sources and findings must be jointly empty or nonempty")
    source_ids: set[str] = set()
    for raw in sources:
        item = _object(raw, {"id", "origin", "excerpt", "retrieved_at"}, "research source")
        source_id = _identifier(item["id"], "research source id")
        if source_id in source_ids:
            raise ContractError("research source ids must be unique")
        source_ids.add(source_id)
        _text(item["origin"], "research source origin", 4_000)
        _text(item["excerpt"], "research source excerpt", 8_000)
        _text(item["retrieved_at"], "research source retrieval time", 128)
    finding_ids: set[str] = set()
    for raw in findings:
        item = _object(raw, {"id", "finding", "source_ids"}, "research finding")
        finding_id = _identifier(item["id"], "research finding id")
        if finding_id in finding_ids:
            raise ContractError("research finding ids must be unique")
        finding_ids.add(finding_id)
        _text(item["finding"], "research finding", 8_000)
        refs = _array(item["source_ids"], "research finding source_ids", nonempty=True)
        if len(refs) != len(set(refs)) or any(ref not in source_ids for ref in refs):
            raise ContractError("research finding attribution is missing or fabricated")

    constraint_ids: set[str] = set()
    for raw in _array(concept["constraints"], "concept constraints"):
        constraint = _object(
            raw, {"id", "description", "value", "basis"}, "concept constraint"
        )
        constraint_id = _identifier(constraint["id"], "concept constraint id")
        if constraint_id in constraint_ids:
            raise ContractError("concept constraint ids must be unique")
        constraint_ids.add(constraint_id)
        _text(constraint["description"], "concept constraint description", 4_000)
        if isinstance(constraint["value"], bool) or not isinstance(
            constraint["value"], (str, int, float)
        ):
            raise ContractError("concept constraint value must be text or a number")
        basis = _object(constraint["basis"], {"kind", "id"}, "concept constraint basis")
        if basis["kind"] == "finding":
            if basis["id"] not in finding_ids:
                raise ContractError("externally grounded constraint lacks a supported finding")
        elif basis["kind"] == "decision":
            if basis["id"] not in decision_ids:
                raise ContractError("deliberate constraint lacks a reasoned decision")
        else:
            raise ContractError("concept constraint basis kind is invalid")
    return json.loads(_canonical(source).decode("utf-8"))


def validate_visual_plan(value: Any, *, component_keys: Sequence[str]) -> dict[str, Any]:
    plan = _object(value, {"schema_version", "kind", "presentation", "roles"}, "visual plan")
    if plan["schema_version"] != 2 or type(plan["schema_version"]) is not int:
        raise ContractError("visual plan schema_version must be 2")
    if plan["kind"] != VISUAL_PLAN_KIND:
        raise ContractError("visual plan kind is invalid")
    _text(plan["presentation"], "visual plan presentation", 4_000)
    roles = _array(plan["roles"], "visual plan roles", nonempty=True)
    if not 2 <= len(roles) <= MAX_VISUAL_ROLES:
        raise ContractError("visual plan must contain from 2 through 20 roles")
    known_components = set(component_keys)
    ids: list[str] = []
    kinds: list[str] = []
    purposes: set[str] = set()
    for index, raw in enumerate(roles):
        role = _object(
            raw,
            {"id", "kind", "purpose", "instruction", "appearance_references", "subject_components"},
            "visual role",
        )
        role_id = _identifier(role["id"], "visual role id")
        if role_id in ids:
            raise ContractError("visual role ids must be unique")
        if role_id.casefold() in {item.casefold() for item in ids}:
            raise ContractError("visual role ids must not create path collisions")
        ids.append(role_id)
        if role["kind"] not in ROLE_KINDS:
            raise ContractError("visual role kind is invalid")
        kinds.append(role["kind"])
        purpose = _text(role["purpose"], "visual role purpose", 2_000).strip().casefold()
        if len(purpose) < 12 or purpose in purposes:
            raise ContractError("each visual role must state distinct useful information")
        purposes.add(purpose)
        _text(role["instruction"], "visual role instruction", 8_000)
        references = _array(role["appearance_references"], "appearance references")
        if len(references) != len(set(references)) or any(ref not in ids[:-1] for ref in references):
            raise ContractError("visual role references must name distinct earlier roles")
        subjects = _array(role["subject_components"], "visual role subject_components")
        if len(subjects) != len(set(subjects)) or any(key not in known_components for key in subjects):
            raise ContractError("visual role names unknown or duplicate component subjects")
        if role["kind"] == "primary-form" and (index != 0 or references):
            raise ContractError("primary-form must be first and have no references")
    if kinds.count("primary-form") != 1 or "signature-experience" not in kinds:
        raise ContractError("visual plan requires exactly one primary-form and a signature-experience")
    return json.loads(_canonical(plan).decode("utf-8"))


def _normalized_research(research: Mapping[str, Any]) -> dict[str, Any]:
    sources = []
    for source in research["sources"]:
        identity = {**source, "excerpt_sha256": _digest(source["excerpt"])}
        identity["source_sha256"] = _digest(identity)
        sources.append(identity)
    findings = []
    for finding in research["findings"]:
        identity = dict(finding)
        identity["finding_sha256"] = _digest(identity)
        findings.append(identity)
    return {"sources": sources, "findings": findings}


@dataclass(frozen=True)
class PreRenderConceptV3:
    round: int
    bindings: Mapping[str, Any]
    authored_inputs: Mapping[str, Any]
    brief: Mapping[str, Any]
    research: Mapping[str, Any]
    drawing_instructions: tuple[Mapping[str, Any], ...]
    descriptor: Mapping[str, Any]
    routed_wish: Mapping[str, Any]
    schema_version: int = 3
    kind: str = PRE_RENDER_CONCEPT_V3_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 3 or type(self.schema_version) is not int or self.kind != PRE_RENDER_CONCEPT_V3_KIND:
            raise ContractError("pre-render Concept v3 protocol is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("pre-render Concept v3 round is invalid")
        bindings = copy_json_mapping(self.bindings, "Concept v3 bindings", nonempty=True)
        authored = copy_json_mapping(self.authored_inputs, "Concept v3 authored inputs", nonempty=True)
        brief = copy_json_mapping(self.brief, "Concept v3 brief", nonempty=True)
        research = copy_json_mapping(self.research, "Concept v3 research")
        descriptor = copy_json_mapping(self.descriptor, "Concept v3 descriptor", nonempty=True)
        routed = copy_json_mapping(self.routed_wish, "Concept v3 routed Wish", nonempty=True)
        instructions = tuple(copy_json_mapping(item, "Concept v3 drawing instruction", nonempty=True) for item in self.drawing_instructions)
        role_ids = [item["id"] for item in instructions]
        if list(descriptor) != role_ids:
            raise ContractError("Concept v3 descriptor order differs from its visual roles")
        for value, label in ((bindings, "bindings"), (authored, "authored_inputs")):
            for key, item in value.items():
                if key.endswith("sha256") and item is not None:
                    require_sha256(item, "Concept v3 %s %s" % (label, key))
        object.__setattr__(self, "bindings", _freeze(dict(bindings)))
        object.__setattr__(self, "authored_inputs", _freeze(dict(authored)))
        object.__setattr__(self, "brief", _freeze(dict(brief)))
        object.__setattr__(self, "research", _freeze(dict(research)))
        object.__setattr__(self, "drawing_instructions", tuple(_freeze(dict(item)) for item in instructions))
        object.__setattr__(self, "descriptor", _freeze(dict(descriptor)))
        object.__setattr__(self, "routed_wish", _freeze(dict(routed)))
        object.__setattr__(self, "concept_sha256", _digest(self._identity()))

    def _identity(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": self.kind, "round": self.round,
            "bindings": _thaw(self.bindings), "authored_inputs": _thaw(self.authored_inputs),
            "brief": _thaw(self.brief), "research": _thaw(self.research),
            "drawing_instructions": _thaw(self.drawing_instructions),
            "descriptor": _thaw(self.descriptor), "routed_wish": _thaw(self.routed_wish),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._identity(), "concept_sha256": self.concept_sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "PreRenderConceptV3":
        expected = {"schema_version", "kind", "round", "bindings", "authored_inputs", "brief", "research", "drawing_instructions", "descriptor", "routed_wish", "concept_sha256"}
        document = _object(value, expected, "pre-render Concept v3")
        created = cls(**{key: document[key] for key in expected - {"concept_sha256"}})
        if created.to_dict() != document:
            raise ContractError("pre-render Concept v3 identity is invalid")
        return created


@dataclass(frozen=True)
class SealedConceptV3:
    source: PreRenderConceptV3
    images: tuple[Mapping[str, Any], ...]
    schema_version: int = 3
    kind: str = SEALED_CONCEPT_V3_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 3 or type(self.schema_version) is not int or self.kind != SEALED_CONCEPT_V3_KIND:
            raise ContractError("sealed Concept v3 protocol is invalid")
        if not isinstance(self.source, PreRenderConceptV3):
            raise ContractError("sealed Concept v3 requires its pre-render source")
        images = tuple(copy_json_mapping(item, "sealed Concept v3 image", nonempty=True) for item in self.images)
        if [item.get("id") for item in images] != list(self.source.descriptor):
            raise ContractError("sealed Concept v3 images differ from the declared role order")
        for item in images:
            if set(item) != {"id", "kind", "purpose", "path", "sha256"}:
                raise ContractError("sealed Concept v3 image fields are invalid")
            declared = self.source.descriptor[item["id"]]
            if item["path"] != declared["path"] or item["kind"] != declared["kind"] or item["purpose"] != declared["purpose"]:
                raise ContractError("sealed Concept v3 image differs from its role")
            require_sha256(item["sha256"], "sealed Concept v3 image sha256")
        object.__setattr__(self, "images", tuple(_freeze(dict(item)) for item in images))
        object.__setattr__(self, "concept_sha256", _digest(self._identity()))

    def _identity(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "kind": self.kind, "source": self.source.to_dict(), "images": _thaw(self.images)}

    def to_dict(self) -> dict[str, Any]:
        return {**self._identity(), "concept_sha256": self.concept_sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "SealedConceptV3":
        document = _object(value, {"schema_version", "kind", "source", "images", "concept_sha256"}, "sealed Concept v3")
        created = cls(source=PreRenderConceptV3.from_mapping(document["source"]), images=tuple(document["images"]), schema_version=document["schema_version"], kind=document["kind"])
        if created.to_dict() != document:
            raise ContractError("sealed Concept v3 identity is invalid")
        return created


@dataclass(frozen=True)
class NormalizedConceptView:
    """Stable Make-facing view shared by sealed Concept v2 and v3."""

    schema_version: int
    concept_sha256: str
    brief: Mapping[str, Any]
    research: Mapping[str, Any]
    visual_roles: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        if self.schema_version not in (2, 3):
            raise ContractError("normalized Concept view schema is unsupported")
        require_sha256(self.concept_sha256, "normalized Concept sha256")
        brief = copy_json_mapping(_thaw(self.brief), "normalized Concept brief", nonempty=True)
        research = copy_json_mapping(_thaw(self.research), "normalized Concept research")
        roles = tuple(copy_json_mapping(_thaw(role), "normalized visual role", nonempty=True) for role in self.visual_roles)
        if not roles or len(roles) > MAX_VISUAL_ROLES:
            raise ContractError("normalized Concept visual role count is invalid")
        object.__setattr__(self, "brief", _freeze(dict(brief)))
        object.__setattr__(self, "research", _freeze(dict(research)))
        object.__setattr__(self, "visual_roles", tuple(_freeze(dict(role)) for role in roles))

    @property
    def component_keys(self) -> tuple[str, ...]:
        return tuple(item["key"] for item in self.brief["components"])


def normalized_concept_view(value: SealedConcept | SealedConceptV3 | Mapping[str, Any], *, root: Any = None) -> NormalizedConceptView:
    """Parse exactly one sealed contract version and expose its stable boundary."""

    if isinstance(value, Mapping):
        version = value.get("schema_version")
        if version == 3:
            value = SealedConceptV3.from_mapping(value)
        elif version == 2:
            if root is None:
                raise ContractError("sealed Concept v2 parsing requires its exact root")
            value = SealedConcept.from_mapping(value, root=root)
        else:
            raise ContractError("sealed Concept mapping version is unsupported")
    if isinstance(value, SealedConceptV3):
        return NormalizedConceptView(
            schema_version=3, concept_sha256=value.concept_sha256,
            brief=value.source.brief, research=value.source.research,
            visual_roles=value.images,
        )
    if not isinstance(value, SealedConcept):
        raise ContractError("normalized Concept reader requires one sealed Concept")
    prompts = value.drawing_instructions
    descriptor = value.descriptor
    roles: list[dict[str, Any]] = []
    for role in ("front", "top", "bottom", "exploded"):
        roles.append({
            "id": role, "kind": "alternate-view", "purpose": "Frozen v1 %s role" % role,
            "path": descriptor[role]["path"], "sha256": descriptor[role]["sha256"],
        })
    for component in value.brief["components"]:
        key = component["key"]
        roles.append({
            "id": "components.%s" % key, "kind": "component",
            "purpose": prompts["components"][key]["instruction"],
            "path": descriptor["components"][key]["path"],
            "sha256": descriptor["components"][key]["sha256"],
        })
    return NormalizedConceptView(
        schema_version=2, concept_sha256=value.concept_sha256,
        brief=value.brief, research=value.research, visual_roles=tuple(roles),
    )


def normalize_authored_concept(
    source_value: Any,
    visual_plan_value: Any,
    *,
    source_path: str,
    source_bytes: bytes,
    visual_plan_path: str,
    visual_plan_bytes: bytes,
    wish: Wish,
    wish_sha256: str,
    assignment: NativeMatchAssignment,
    invented: NativeInvented,
    round: int,
    standing_concept_sha256: str | None = None,
    revision_input_sha256: str | None = None,
) -> PreRenderConceptV3:
    source = validate_authored_source(source_value)
    components = source["concept"]["components"]
    plan = validate_visual_plan(visual_plan_value, component_keys=[item["key"] for item in components])
    if not isinstance(source_bytes, bytes) or not source_bytes or not isinstance(visual_plan_bytes, bytes) or not visual_plan_bytes:
        raise ContractError("simplified Concept authored bytes are missing")
    if source["selected_inventor_id"] != assignment.selected_inventor_id or source["ranking"] != [item.to_dict() for item in assignment.ranking]:
        raise ContractError("simplified Invent selection differs from its assignment")
    if source["concept"] != invented.to_dict()["concept"] or source["research"] != invented.to_dict()["research"]:
        raise ContractError("simplified Invent content differs from its Invented contract")
    if wish_sha256 != assignment.wish_sha256:
        raise ContractError("simplified Concept Wish binding differs from its assignment")
    revision = (standing_concept_sha256, revision_input_sha256)
    if (round == 1 and any(item is not None for item in revision)) or (round > 1 and any(item is None for item in revision)):
        raise ContractError("simplified Concept revision bindings are invalid")
    for item in revision:
        if item is not None:
            require_sha256(item, "simplified Concept revision sha256")
    constraints = source["concept"]["constraints"]
    constraint_block = {item["id"]: {"description": item["description"], "value": item["value"]} for item in constraints}
    roles = plan["roles"]
    instructions = tuple({**role, "presentation": plan["presentation"]} for role in roles)
    descriptor = {
        role["id"]: {
            "kind": role["kind"], "purpose": role["purpose"],
            "path": "images/%s.png" % role["id"],
        }
        for role in roles
    }
    bindings = {
        "wish_sha256": wish_sha256, "assignment_sha256": assignment.assignment_sha256,
        "taste_sha256": assignment.selected_taste_sha256,
        "blueprint_sha256": assignment.blueprint_sha256,
        "invented_sha256": invented.invented_sha256,
        "standing_concept_sha256": standing_concept_sha256,
        "revision_input_sha256": revision_input_sha256,
    }
    authored = {
        "source_path": source_path, "source_sha256": _digest(source_bytes),
        "visual_plan_path": visual_plan_path, "visual_plan_sha256": _digest(visual_plan_bytes),
    }
    routed = {
        "wish_sha256": wish_sha256, "product_id": wish.product_id, "objective": wish.objective,
        "context": dict(wish.context), "constraints": constraint_block,
    }
    routed["routed_wish_sha256"] = _digest(routed)
    return PreRenderConceptV3(
        round=round, bindings=bindings, authored_inputs=authored,
        brief=source["concept"], research=_normalized_research(source["research"]),
        drawing_instructions=instructions, descriptor=descriptor, routed_wish=routed,
    )


__all__ = [
    "MAX_VISUAL_ROLES", "PRE_RENDER_CONCEPT_V3_KIND",
    "ROLE_KINDS", "SEALED_CONCEPT_V3_KIND", "VISUAL_PLAN_KIND",
    "PreRenderConceptV3", "SealedConceptV3", "normalize_authored_concept",
    "NormalizedConceptView", "normalized_concept_view", "validate_authored_source",
    "validate_visual_plan",
]
