"""Deterministic rule checks over an authored Concept brief.

These are the checks `workshop/concept-stage`, `workshop/concept-images`, and
`workshop/wish-research` ask a host gate to settle: that a brief decided
something about this Wish, that every fact it states is attributable, that
every component is genuinely specified, and that the drawing instructions
form a consistent, complete, and safely ordered image set. Every refusal
raises :class:`~workshop.errors.ContractError` naming the rule it broke; this
module never repairs, defaults, or supplies a missing fact.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from workshop.concept.native import ConceptTree, OVERALL_IMAGE_ROLES
from workshop.errors import ContractError
from workshop.wish import Wish


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_REQUIRED_TOP_LEVEL_FACTS = ("object", "category", "envelope_mm", "wall_thickness_mm", "print_stance")
_COMPONENT_FIELDS = frozenset(
    ("key", "name", "purpose", "form", "dimensions_mm", "placement", "interfaces")
)
_DIMENSION_FIELDS = frozenset(("length_mm", "width_mm", "height_mm"))
_EXPECTED_OVERALL_REFERENCES = {
    "front": (),
    "top": ("front",),
    "bottom": ("front",),
    "exploded": ("front", "top", "bottom"),
}
_COMPONENT_REFERENCES = ("front",)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ContractError("%s must be a bounded lowercase identifier" % label)
    return value


def _bounded_text(value: Any, label: str, maximum: int = 4_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty text" % label)
    return value


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ContractError("%s must be a positive number" % label)
    return float(value)


def _dimensions_mm(value: Any, label: str) -> Mapping[str, float]:
    if not isinstance(value, Mapping) or set(value) != _DIMENSION_FIELDS:
        raise ContractError("%s must state length_mm, width_mm, and height_mm" % label)
    return {
        field: _positive_number(value[field], "%s %s" % (label, field))
        for field in _DIMENSION_FIELDS
    }


def _validate_features(brief: Mapping[str, Any]) -> Mapping[str, str]:
    features = brief.get("features")
    if not isinstance(features, list) or not features:
        raise ContractError("concept brief must state at least one distinctive feature")
    by_id: dict[str, str] = {}
    for feature in features:
        if not isinstance(feature, Mapping) or set(feature) != {"id", "text"}:
            raise ContractError("concept brief feature fields are invalid")
        feature_id = _identifier(feature["id"], "concept brief feature id")
        if feature_id in by_id:
            raise ContractError("concept brief feature ids must be unique")
        by_id[feature_id] = _bounded_text(feature["text"], "concept brief feature text", 2_000)
    return by_id


def _validate_components(brief: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    components = brief.get("components")
    if not isinstance(components, list) or not components:
        raise ContractError("concept brief must name at least one component")
    by_key: dict[str, Mapping[str, Any]] = {}
    for component in components:
        if not isinstance(component, Mapping) or set(component) != _COMPONENT_FIELDS:
            raise ContractError(
                "concept brief component must state its form, bounding dimensions, "
                "placement, and interfaces, not merely a name and purpose"
            )
        key = _identifier(component["key"], "concept brief component key")
        if key in by_key:
            raise ContractError("concept brief component keys must be unique")
        _bounded_text(component["name"], "concept brief component %s name" % key, 200)
        _bounded_text(component["purpose"], "concept brief component %s purpose" % key)
        _bounded_text(component["form"], "concept brief component %s form" % key)
        _dimensions_mm(
            component["dimensions_mm"],
            "concept brief component %s dimensions_mm" % key,
        )
        _bounded_text(component["placement"], "concept brief component %s placement" % key)
        _bounded_text(component["interfaces"], "concept brief component %s interfaces" % key)
        by_key[key] = component
    return by_key


def _validate_print_stance(brief: Mapping[str, Any]) -> None:
    stance = brief.get("print_stance")
    if not isinstance(stance, Mapping) or set(stance) != {
        "orientation",
        "supports_required",
        "support_notes",
    }:
        raise ContractError(
            "concept brief must state a print_stance with orientation and support use"
        )
    _bounded_text(stance["orientation"], "concept brief print_stance orientation", 1_000)
    if type(stance["supports_required"]) is not bool:
        raise ContractError("concept brief print_stance supports_required must be boolean")
    _bounded_text(stance["support_notes"], "concept brief print_stance support_notes", 2_000)


def _validate_fit_target(brief: Mapping[str, Any]) -> bool:
    fit_target = brief.get("fit_target")
    if fit_target is None:
        return False
    if not isinstance(fit_target, Mapping) or set(fit_target) != {
        "target",
        "dimensions_mm",
        "clearance_mm",
    }:
        raise ContractError(
            "concept brief fit_target must state its target, dimensions, and clearance"
        )
    _bounded_text(fit_target["target"], "concept brief fit_target target", 2_000)
    _dimensions_mm(fit_target["dimensions_mm"], "concept brief fit_target dimensions_mm")
    clearance = fit_target["clearance_mm"]
    if isinstance(clearance, bool) or not isinstance(clearance, (int, float)) or clearance < 0:
        raise ContractError("concept brief fit_target clearance_mm must be a non-negative number")
    return True


def _validate_facts(
    brief: Mapping[str, Any],
    research: Mapping[str, Any],
    *,
    feature_ids: Mapping[str, str],
    component_keys: Mapping[str, Mapping[str, Any]],
    has_fit_target: bool,
) -> None:
    sources = research.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ContractError("concept research must record at least one source")
    source_ids = set()
    for source in sources:
        if not isinstance(source, Mapping) or set(source) != {
            "id",
            "origin",
            "excerpt",
            "excerpt_sha256",
            "retrieved_at",
        }:
            raise ContractError("concept research source fields are invalid")
        source_id = _identifier(source["id"], "concept research source id")
        if source_id in source_ids:
            raise ContractError("concept research source ids must be unique")
        source_ids.add(source_id)

    required_fields = set(_REQUIRED_TOP_LEVEL_FACTS)
    if has_fit_target:
        required_fields.add("fit_target")
    required_fields |= {"features.%s" % feature_id for feature_id in feature_ids}
    required_fields |= {"components.%s" % key for key in component_keys}

    facts = brief.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ContractError("concept brief must attribute every fact it states")
    seen_fields: set[str] = set()
    for fact in facts:
        if not isinstance(fact, Mapping) or set(fact) != {
            "field",
            "source_id",
            "assumption_reason",
        }:
            raise ContractError("concept brief fact fields are invalid")
        field_name = fact["field"]
        if not isinstance(field_name, str) or field_name not in required_fields:
            raise ContractError(
                "concept brief fact names a field this brief does not require: %s"
                % field_name
            )
        if field_name in seen_fields:
            raise ContractError(
                "concept brief fact %s is attributed more than once" % field_name
            )
        seen_fields.add(field_name)
        source_id = fact["source_id"]
        reason = fact["assumption_reason"]
        has_source = isinstance(source_id, str) and bool(source_id)
        has_reason = isinstance(reason, str) and bool(reason.strip())
        if has_source == has_reason:
            raise ContractError(
                "concept brief fact %s must name exactly one of a recorded source "
                "or a recorded decision" % field_name
            )
        if has_source and source_id not in source_ids:
            raise ContractError(
                "concept brief fact %s names a source the research did not record"
                % field_name
            )
    missing = required_fields - seen_fields
    if missing:
        raise ContractError(
            "concept brief leaves facts unattributed: %s" % sorted(missing)
        )


def _validate_no_restated_objective(
    feature_ids: Mapping[str, str], wish: Wish
) -> None:
    objective = _normalize(wish.objective)
    genuine = [
        text for text in feature_ids.values() if _normalize(text) != objective
    ]
    if not genuine:
        raise ContractError(
            "concept brief's only distinctive feature restates the Wish objective "
            "and decides nothing"
        )


def _validate_drawing_instructions(
    drawing_instructions: Mapping[str, Any],
    *,
    component_keys: Mapping[str, Mapping[str, Any]],
) -> None:
    expected_top = set(OVERALL_IMAGE_ROLES) | {"components"}
    if set(drawing_instructions) != expected_top:
        raise ContractError(
            "concept drawing instructions must cover exactly front, top, bottom, "
            "exploded, and components"
        )
    for role, expected_references in _EXPECTED_OVERALL_REFERENCES.items():
        entry = drawing_instructions[role]
        if not isinstance(entry, Mapping) or set(entry) != {"instruction", "references"}:
            raise ContractError("concept drawing instruction for %s is invalid" % role)
        _bounded_text(entry["instruction"], "concept drawing instruction for %s" % role, 8_000)
        references = entry["references"]
        if not isinstance(references, list) or tuple(references) != expected_references:
            raise ContractError(
                "concept drawing instruction for %s must reference exactly %s, "
                "roles drawn before it" % (role, list(expected_references))
            )

    exploded_text = _normalize(drawing_instructions["exploded"]["instruction"])
    component_instructions = drawing_instructions["components"]
    if not isinstance(component_instructions, Mapping) or set(component_instructions) != set(
        component_keys
    ):
        raise ContractError(
            "concept must author exactly one drawing instruction per brief component, "
            "and no instruction for an unknown role"
        )
    for key, component in component_keys.items():
        entry = component_instructions[key]
        if not isinstance(entry, Mapping) or set(entry) != {"instruction", "references"}:
            raise ContractError(
                "concept drawing instruction for component %s is invalid" % key
            )
        _bounded_text(
            entry["instruction"], "concept drawing instruction for component %s" % key, 8_000
        )
        references = entry["references"]
        if not isinstance(references, list) or tuple(references) != _COMPONENT_REFERENCES:
            raise ContractError(
                "concept drawing instruction for component %s must reference exactly "
                "%s for appearance only, and never exploded" % (key, list(_COMPONENT_REFERENCES))
            )
        component_name = _normalize(component["name"])
        if component_name not in exploded_text:
            raise ContractError(
                "concept exploded drawing instruction must name every component in "
                "the brief, missing %s" % key
            )


def _validate_descriptor(
    descriptor: Mapping[str, Any], *, component_keys: Mapping[str, Mapping[str, Any]]
) -> None:
    expected_top = set(OVERALL_IMAGE_ROLES) | {"components"}
    if set(descriptor) != expected_top:
        raise ContractError(
            "concept descriptor must cover exactly front, top, bottom, exploded, "
            "and components"
        )
    components = descriptor["components"]
    if not isinstance(components, Mapping) or set(components) != set(component_keys):
        raise ContractError(
            "concept descriptor must name exactly one image per brief component"
        )


def evaluate_concept_brief(tree: ConceptTree, *, wish: Wish) -> Mapping[str, Any]:
    """Settle every structural rule a Concept brief must satisfy.

    Raises :class:`ContractError` naming the first rule broken. Returns a
    mapping of the facts checked, suitable for the gate's evidence record.
    """

    brief = tree.brief
    for field_name in ("object", "category"):
        if field_name not in brief:
            raise ContractError("concept brief is missing its %s" % field_name)
        _bounded_text(brief[field_name], "concept brief %s" % field_name, 2_000)
    if "envelope_mm" not in brief:
        raise ContractError("concept brief is missing its envelope_mm")
    _dimensions_mm(brief["envelope_mm"], "concept brief envelope_mm")
    if "wall_thickness_mm" not in brief:
        raise ContractError("concept brief is missing its wall_thickness_mm")
    _positive_number(brief["wall_thickness_mm"], "concept brief wall_thickness_mm")
    _validate_print_stance(brief)
    feature_ids = _validate_features(brief)
    component_keys = _validate_components(brief)
    has_fit_target = _validate_fit_target(brief)
    _validate_no_restated_objective(feature_ids, wish)
    _validate_facts(
        brief,
        tree.research,
        feature_ids=feature_ids,
        component_keys=component_keys,
        has_fit_target=has_fit_target,
    )
    findings = tree.research.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ContractError("concept research must state at least one finding")
    _validate_drawing_instructions(
        tree.drawing_instructions, component_keys=component_keys
    )
    _validate_descriptor(tree.descriptor, component_keys=component_keys)
    return {
        "object": brief["object"],
        "component_keys": sorted(component_keys),
        "feature_count": len(feature_ids),
        "has_fit_target": has_fit_target,
        "source_count": len(tree.research["sources"]),
    }


__all__ = ["evaluate_concept_brief"]
