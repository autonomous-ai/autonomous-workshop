"""Fixed-view Concept authoring and normalized Concept v4 contracts.

The native Manager owns the consolidated physical source, one shared appearance
description, and concise depiction notes.  This module deterministically derives
the fixed CAD-reconstruction views and their transport prompts; it does not
choose product geometry or judge returned pixels.
"""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import NativeMatchAssignment
from workshop.wish import Wish

from .v3 import MAX_VISUAL_ROLES, validate_authored_source


FIXED_VIEW_INSTRUCTIONS_KIND = "autonomous-workshop.fixed-concept-view-instructions"
PRE_RENDER_CONCEPT_V4_KIND = "autonomous-workshop.concept-pre-render"
SEALED_CONCEPT_V4_KIND = "autonomous-workshop.concept-sealed"
FIXED_PROMPT_PROTOCOL_VERSION = "cad-reconstruction-views-v1"
FIXED_OVERALL_ROLES = ("front", "top", "bottom", "exploded")
MAX_FIXED_COMPONENTS = MAX_VISUAL_ROLES - len(FIXED_OVERALL_ROLES)

FIXED_PRESENTATION_PROMPT = (
    "Show exactly one complete subject, centered and fully in frame, as a simple "
    "orthographic-like product design study at a useful consistent scale and "
    "orientation. Use a pure white or very light neutral background, flat neutral "
    "lighting, restrained matte materials, and crisp legible silhouettes, edges, "
    "part boundaries, and construction. No perspective drama, wide-angle "
    "distortion, depth of field, reflections, cast-shadow staging, or scene. No text, "
    "dimension annotations, arrows, labels, logos, watermarks, people, hands, fit "
    "targets, held objects, mounted objects, or unrelated props."
)

_ROLE_PROMPTS = {
    "front": (
        "Create the FRONT view. Face the declared front directly toward the camera "
        "and establish the complete product's shared appearance and proportions."
    ),
    "top": (
        "Reference image 1 is the FRONT view. Depict the SAME complete product, "
        "unchanged, directly from above. Only the camera direction changes."
    ),
    "bottom": (
        "Reference image 1 is the FRONT view. Depict the SAME complete product, "
        "unchanged, directly from below. Only the camera direction changes; keep "
        "the underside and declared print stance legible."
    ),
    "exploded": (
        "Reference images 1, 2, and 3 are the FRONT, TOP, and BOTTOM views of the "
        "same product. Create one EXPLODED view containing the complete product set. "
        "Preserve every shape, proportion, feature, material, and finish. Separate "
        "every named component along understandable assembly axes so every part and "
        "mating surface is complete and unobscured."
    ),
    "component": (
        "Reference image 1 is the EXPLODED view of the complete product. Show only "
        "the named component, alone and complete, preserving its exact appearance, "
        "orientation, form, measurements, mating interfaces, and assembly relationship."
    ),
}

_ROLE_PURPOSES = {
    "front": "Direct front reference for overall silhouette and proportions",
    "top": "Direct top reference for overall footprint and upper construction",
    "bottom": "Direct bottom reference for underside construction and print stance",
    "exploded": "Complete unobscured assembly and component relationship reference",
    "component": "Isolated component form and mating-interface reference",
}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("fixed-view Concept values must be finite JSON") from exc


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


def _text(value: Any, label: str, maximum: int = 8_000) -> str:
    return bounded_text(value, label, maximum)


def _safe_component_key(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or PurePosixPath(value).name != value
        or "/" in value
        or "\\" in value
        or value in (".", "..")
    ):
        raise ContractError("%s must be a safe component key" % label)
    # Source validation already limits keys to lowercase kebab identifiers.
    return value


def validate_fixed_view_instructions(
    value: Any, *, component_keys: Sequence[str]
) -> dict[str, Any]:
    """Validate the exact fixed-key second authored input."""

    document = _object(
        value,
        {"schema_version", "kind", "appearance", "views", "components"},
        "fixed-view instructions",
    )
    if document["schema_version"] != 3 or type(document["schema_version"]) is not int:
        raise ContractError("fixed-view instructions schema_version must be 3")
    if document["kind"] != FIXED_VIEW_INSTRUCTIONS_KIND:
        raise ContractError("fixed-view instructions kind is invalid")
    _text(document["appearance"], "fixed-view appearance", 4_000)
    views = _object(
        document["views"], set(FIXED_OVERALL_ROLES), "fixed-view overall notes"
    )
    for role in FIXED_OVERALL_ROLES:
        _text(views[role], "fixed-view %s note" % role, 4_000)
    normalized_keys = tuple(
        _safe_component_key(key, "fixed-view component key") for key in component_keys
    )
    if not normalized_keys or len(normalized_keys) > MAX_FIXED_COMPONENTS:
        raise ContractError(
            "fixed-view Concept must contain from 1 through %d components"
            % MAX_FIXED_COMPONENTS
        )
    if len(normalized_keys) != len(set(normalized_keys)):
        raise ContractError("fixed-view component keys must be unique")
    raw_components = document["components"]
    if (
        not isinstance(raw_components, Mapping)
        or set(raw_components) != set(normalized_keys)
        or len(raw_components) != len(normalized_keys)
    ):
        raise ContractError(
            "fixed-view component notes must exactly match source components"
        )
    components = copy_json_mapping(
        raw_components, "fixed-view component notes", nonempty=True
    )
    for key, note in components.items():
        _text(note, "fixed-view component %s note" % key, 4_000)
    exploded = views["exploded"].casefold()
    missing = [key for key in normalized_keys if key.casefold() not in exploded]
    if missing:
        raise ContractError(
            "fixed-view exploded note must name every component: %s"
            % ", ".join(missing)
        )
    # Preserve source component order in the returned author input. Canonical JSON
    # sorting is used for identities, but order is part of this authoring contract.
    return {
        "schema_version": 3,
        "kind": FIXED_VIEW_INSTRUCTIONS_KIND,
        "appearance": document["appearance"],
        "views": {role: views[role] for role in FIXED_OVERALL_ROLES},
        "components": {key: components[key] for key in normalized_keys},
    }


def fixed_prompt_protocol_sha256() -> str:
    return _digest(
        {
            "version": FIXED_PROMPT_PROTOCOL_VERSION,
            "presentation": FIXED_PRESENTATION_PROMPT,
            "roles": _ROLE_PROMPTS,
        }
    )


def _overall_facts(concept: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "object": concept["object"],
        "category": concept["category"],
        "summary": concept["summary"],
        "envelope_mm": concept["envelope_mm"],
        "print_stance": concept["print_stance"],
        "non_negotiable_constraints": concept["non_negotiable_constraints"],
    }


def derive_fixed_roles(
    concept: Mapping[str, Any], instructions: Mapping[str, Any]
) -> tuple[dict[str, Any], ...]:
    """Derive exact prompts, references, paths, and role facts."""

    components = list(concept["components"])
    component_keys = [item["key"] for item in components]
    validated = validate_fixed_view_instructions(
        instructions, component_keys=component_keys
    )
    appearance = validated["appearance"]
    overall_facts = _overall_facts(concept)
    result: list[dict[str, Any]] = []
    for role in FIXED_OVERALL_ROLES:
        references: list[str]
        facts: dict[str, Any] = dict(overall_facts)
        if role == "front":
            references = []
        elif role in ("top", "bottom"):
            references = ["front"]
        else:
            references = ["front", "top", "bottom"]
            facts["components"] = components
        result.append(
            {
                "id": role,
                "kind": role,
                "purpose": _ROLE_PURPOSES[role],
                "instruction": "%s\n\n%s" % (_ROLE_PROMPTS[role], FIXED_PRESENTATION_PROMPT),
                "appearance_references": references,
                "subject_components": component_keys if role == "exploded" else component_keys,
                "appearance": appearance,
                "note": validated["views"][role],
                "normalized_facts": facts,
                "prompt_protocol_version": FIXED_PROMPT_PROTOCOL_VERSION,
            }
        )
    for component in components:
        key = component["key"]
        result.append(
            {
                "id": "component:%s" % key,
                "kind": "component",
                "purpose": "%s: %s" % (_ROLE_PURPOSES["component"], key),
                "instruction": "%s\n\n%s" % (_ROLE_PROMPTS["component"], FIXED_PRESENTATION_PROMPT),
                "appearance_references": ["exploded"],
                "subject_components": [key],
                "appearance": appearance,
                "note": validated["components"][key],
                "normalized_facts": component,
                "prompt_protocol_version": FIXED_PROMPT_PROTOCOL_VERSION,
            }
        )
    if len(result) != 4 + len(components) or len(result) > MAX_VISUAL_ROLES:
        raise ContractError("fixed-view role count is invalid")
    return tuple(result)


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


def _author_source_manifest(
    *, source_path: str, source_bytes_count: int, source_sha256: str,
    visual_instructions_path: str, visual_instructions_bytes_count: int,
    visual_instructions_sha256: str,
) -> dict[str, Any]:
    entries = []
    for path, count, digest in (
        (source_path, source_bytes_count, source_sha256),
        (visual_instructions_path, visual_instructions_bytes_count, visual_instructions_sha256),
    ):
        candidate = PurePosixPath(path) if isinstance(path, str) else PurePosixPath(".")
        if (
            not isinstance(path, str) or not path or candidate.is_absolute()
            or ".." in candidate.parts or candidate.as_posix() != path
        ):
            raise ContractError("Concept v4 authored input path is unsafe")
        if type(count) is not int or count <= 0:
            raise ContractError("Concept v4 authored input byte count is invalid")
        require_sha256(digest, "Concept v4 authored input sha256")
        entries.append({"path": path, "bytes": count, "sha256": digest})
    if source_path == visual_instructions_path:
        raise ContractError("Concept v4 authored input paths must be distinct")
    entries.sort(key=lambda item: item["path"])
    identity = {"schema_version": 1, "entries": entries}
    return {**identity, "artifact_sha256": _digest(identity)}


@dataclass(frozen=True)
class PreRenderConceptV4:
    round: int
    bindings: Mapping[str, Any]
    authored_inputs: Mapping[str, Any]
    author_source_manifest: Mapping[str, Any]
    prompt_protocol_sha256: str
    brief: Mapping[str, Any]
    research: Mapping[str, Any]
    drawing_instructions: tuple[Mapping[str, Any], ...]
    descriptor: Mapping[str, Any]
    routed_wish: Mapping[str, Any]
    schema_version: int = 4
    kind: str = PRE_RENDER_CONCEPT_V4_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 4 or type(self.schema_version) is not int or self.kind != PRE_RENDER_CONCEPT_V4_KIND:
            raise ContractError("pre-render Concept v4 protocol is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("pre-render Concept v4 round is invalid")
        require_sha256(self.prompt_protocol_sha256, "Concept v4 prompt protocol sha256")
        if self.prompt_protocol_sha256 != fixed_prompt_protocol_sha256():
            raise ContractError("Concept v4 prompt protocol identity is invalid")
        bindings = copy_json_mapping(self.bindings, "Concept v4 bindings", nonempty=True)
        authored = copy_json_mapping(self.authored_inputs, "Concept v4 authored inputs", nonempty=True)
        manifest = copy_json_mapping(self.author_source_manifest, "Concept v4 source manifest", nonempty=True)
        brief = copy_json_mapping(self.brief, "Concept v4 brief", nonempty=True)
        research = copy_json_mapping(self.research, "Concept v4 research")
        descriptor = copy_json_mapping(self.descriptor, "Concept v4 descriptor", nonempty=True)
        routed = copy_json_mapping(self.routed_wish, "Concept v4 routed Wish", nonempty=True)
        roles = tuple(copy_json_mapping(item, "Concept v4 role", nonempty=True) for item in self.drawing_instructions)
        role_ids = [item["id"] for item in roles]
        expected_ids = [*FIXED_OVERALL_ROLES, *("component:%s" % item["key"] for item in brief["components"])]
        if (
            role_ids != expected_ids
            or set(descriptor) != set(expected_ids)
            or len(descriptor) != len(expected_ids)
        ):
            raise ContractError("Concept v4 roles differ from the fixed component-derived set")
        expected_role_fields = {
            "id", "kind", "purpose", "instruction", "appearance_references",
            "subject_components", "appearance", "note", "normalized_facts",
            "prompt_protocol_version",
        }
        expected_references = {
            "front": [], "top": ["front"], "bottom": ["front"],
            "exploded": ["front", "top", "bottom"],
        }
        observed_paths: list[str] = []
        for role in roles:
            role_id = role["id"]
            component_role = role_id.startswith("component:")
            expected_kind = "component" if component_role else role_id
            expected_path = (
                "images/components/%s.png" % role_id.split(":", 1)[1]
                if component_role else "images/%s.png" % role_id
            )
            expected_role_references = (
                ["exploded"] if component_role else expected_references[role_id]
            )
            declared = descriptor[role_id]
            if (
                set(role) != expected_role_fields
                or role["kind"] != expected_kind
                or role["appearance_references"] != expected_role_references
                or role["prompt_protocol_version"] != FIXED_PROMPT_PROTOCOL_VERSION
                or set(declared) != {"kind", "purpose", "path"}
                or declared["kind"] != expected_kind
                or declared["purpose"] != role["purpose"]
                or declared["path"] != expected_path
            ):
                raise ContractError("Concept v4 role or path violates the fixed protocol")
            observed_paths.append(declared["path"])
        if len(observed_paths) != len(set(observed_paths)):
            raise ContractError("Concept v4 role paths must be unique")
        expected_manifest = _author_source_manifest(
            source_path=authored["source_path"], source_bytes_count=authored["source_bytes"],
            source_sha256=authored["source_sha256"],
            visual_instructions_path=authored["visual_instructions_path"],
            visual_instructions_bytes_count=authored["visual_instructions_bytes"],
            visual_instructions_sha256=authored["visual_instructions_sha256"],
        )
        if manifest != expected_manifest:
            raise ContractError("Concept v4 author-source manifest identity is invalid")
        object.__setattr__(self, "bindings", _freeze(dict(bindings)))
        object.__setattr__(self, "authored_inputs", _freeze(dict(authored)))
        object.__setattr__(self, "author_source_manifest", _freeze(dict(manifest)))
        object.__setattr__(self, "brief", _freeze(dict(brief)))
        object.__setattr__(self, "research", _freeze(dict(research)))
        object.__setattr__(self, "drawing_instructions", tuple(_freeze(dict(item)) for item in roles))
        object.__setattr__(self, "descriptor", _freeze(dict(descriptor)))
        object.__setattr__(self, "routed_wish", _freeze(dict(routed)))
        object.__setattr__(self, "concept_sha256", _digest(self._identity()))

    def _identity(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": self.kind, "round": self.round,
            "bindings": _thaw(self.bindings), "authored_inputs": _thaw(self.authored_inputs),
            "author_source_manifest": _thaw(self.author_source_manifest),
            "prompt_protocol_sha256": self.prompt_protocol_sha256,
            "brief": _thaw(self.brief), "research": _thaw(self.research),
            "drawing_instructions": _thaw(self.drawing_instructions),
            "descriptor": _thaw(self.descriptor), "routed_wish": _thaw(self.routed_wish),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._identity(), "concept_sha256": self.concept_sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "PreRenderConceptV4":
        expected = {
            "schema_version", "kind", "round", "bindings", "authored_inputs",
            "author_source_manifest", "prompt_protocol_sha256", "brief", "research",
            "drawing_instructions", "descriptor", "routed_wish", "concept_sha256",
        }
        document = _object(value, expected, "pre-render Concept v4")
        created = cls(**{key: document[key] for key in expected - {"concept_sha256"}})
        if created.to_dict() != document:
            raise ContractError("pre-render Concept v4 identity is invalid")
        return created


@dataclass(frozen=True)
class SealedConceptV4:
    source: PreRenderConceptV4
    images: tuple[Mapping[str, Any], ...]
    schema_version: int = 4
    kind: str = SEALED_CONCEPT_V4_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 4 or type(self.schema_version) is not int or self.kind != SEALED_CONCEPT_V4_KIND:
            raise ContractError("sealed Concept v4 protocol is invalid")
        if not isinstance(self.source, PreRenderConceptV4):
            raise ContractError("sealed Concept v4 requires its pre-render source")
        images = tuple(copy_json_mapping(item, "sealed Concept v4 image", nonempty=True) for item in self.images)
        if [item.get("id") for item in images] != [item["id"] for item in self.source.drawing_instructions]:
            raise ContractError("sealed Concept v4 images differ from the fixed role order")
        for item in images:
            if set(item) != {"id", "kind", "purpose", "path", "sha256"}:
                raise ContractError("sealed Concept v4 image fields are invalid")
            declared = self.source.descriptor[item["id"]]
            if item["path"] != declared["path"] or item["kind"] != declared["kind"] or item["purpose"] != declared["purpose"]:
                raise ContractError("sealed Concept v4 image differs from its role")
            require_sha256(item["sha256"], "sealed Concept v4 image sha256")
        object.__setattr__(self, "images", tuple(_freeze(dict(item)) for item in images))
        object.__setattr__(self, "concept_sha256", _digest(self._identity()))

    def _identity(self) -> dict[str, Any]:
        return {"schema_version": 4, "kind": self.kind, "source": self.source.to_dict(), "images": _thaw(self.images)}

    def to_dict(self) -> dict[str, Any]:
        return {**self._identity(), "concept_sha256": self.concept_sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "SealedConceptV4":
        document = _object(value, {"schema_version", "kind", "source", "images", "concept_sha256"}, "sealed Concept v4")
        created = cls(source=PreRenderConceptV4.from_mapping(document["source"]), images=tuple(document["images"]), schema_version=document["schema_version"], kind=document["kind"])
        if created.to_dict() != document:
            raise ContractError("sealed Concept v4 identity is invalid")
        return created


def normalize_fixed_view_concept(
    source_value: Any,
    instructions_value: Any,
    *,
    source_path: str,
    source_bytes: bytes,
    visual_instructions_path: str,
    visual_instructions_bytes: bytes,
    wish: Wish,
    wish_sha256: str,
    assignment: NativeMatchAssignment,
    invented: NativeInvented,
    round: int,
    standing_concept_sha256: str | None = None,
    revision_input_sha256: str | None = None,
) -> PreRenderConceptV4:
    source = validate_authored_source(source_value)
    if not isinstance(source_bytes, bytes) or not source_bytes or not isinstance(visual_instructions_bytes, bytes) or not visual_instructions_bytes:
        raise ContractError("fixed-view Concept authored bytes are missing")
    if source["selected_inventor_id"] != assignment.selected_inventor_id or source["ranking"] != [item.to_dict() for item in assignment.ranking]:
        raise ContractError("fixed-view Invent selection differs from its assignment")
    if source["concept"] != invented.to_dict()["concept"] or source["research"] != invented.to_dict()["research"]:
        raise ContractError("fixed-view Invent content differs from its Invented contract")
    if wish_sha256 != assignment.wish_sha256:
        raise ContractError("fixed-view Concept Wish binding differs from its assignment")
    revision = (standing_concept_sha256, revision_input_sha256)
    if (round == 1 and any(item is not None for item in revision)) or (round > 1 and any(item is None for item in revision)):
        raise ContractError("fixed-view Concept revision bindings are invalid")
    for item in revision:
        if item is not None:
            require_sha256(item, "fixed-view Concept revision sha256")
    concept = source["concept"]
    roles = derive_fixed_roles(concept, instructions_value)
    descriptor = {}
    for role in roles:
        path = (
            "images/components/%s.png" % role["id"].split(":", 1)[1]
            if role["kind"] == "component"
            else "images/%s.png" % role["id"]
        )
        descriptor[role["id"]] = {
            "kind": role["kind"], "purpose": role["purpose"], "path": path,
        }
    constraints = concept["constraints"]
    constraint_block = {item["id"]: {"description": item["description"], "value": item["value"]} for item in constraints}
    if len(_canonical(constraint_block)) > 12_000:
        raise ContractError("normalized Concept constraint block is oversized")
    bindings = {
        "wish_sha256": wish_sha256, "assignment_sha256": assignment.assignment_sha256,
        "taste_sha256": assignment.selected_taste_sha256,
        "blueprint_sha256": assignment.blueprint_sha256,
        "invented_sha256": invented.invented_sha256,
        "standing_concept_sha256": standing_concept_sha256,
        "revision_input_sha256": revision_input_sha256,
    }
    authored = {
        "source_path": source_path, "source_bytes": len(source_bytes), "source_sha256": _digest(source_bytes),
        "visual_instructions_path": visual_instructions_path,
        "visual_instructions_bytes": len(visual_instructions_bytes),
        "visual_instructions_sha256": _digest(visual_instructions_bytes),
    }
    manifest = _author_source_manifest(
        source_path=source_path, source_bytes_count=len(source_bytes), source_sha256=authored["source_sha256"],
        visual_instructions_path=visual_instructions_path,
        visual_instructions_bytes_count=len(visual_instructions_bytes),
        visual_instructions_sha256=authored["visual_instructions_sha256"],
    )
    routed = {
        "wish_sha256": wish_sha256, "product_id": wish.product_id,
        "objective": wish.objective, "context": dict(wish.context),
        "constraints": constraint_block,
    }
    routed["routed_wish_sha256"] = _digest(routed)
    return PreRenderConceptV4(
        round=round, bindings=bindings, authored_inputs=authored,
        author_source_manifest=manifest,
        prompt_protocol_sha256=fixed_prompt_protocol_sha256(),
        brief=concept, research=_normalized_research(source["research"]),
        drawing_instructions=roles, descriptor=descriptor, routed_wish=routed,
    )


def seal_pre_render_concept_v4(
    source: PreRenderConceptV4, image_bytes: Mapping[str, bytes]
) -> SealedConceptV4:
    if not isinstance(source, PreRenderConceptV4) or not isinstance(image_bytes, Mapping):
        raise ContractError("Concept v4 sealing requires pre-render source and image bytes")
    role_order = [item["id"] for item in source.drawing_instructions]
    if list(image_bytes) != role_order:
        raise ContractError("Concept v4 image bytes differ from the fixed role order")
    images = []
    for role_id in role_order:
        descriptor = source.descriptor[role_id]
        content = image_bytes[role_id]
        if not isinstance(content, bytes) or not content:
            raise ContractError("Concept v4 image bytes are missing")
        images.append({
            "id": role_id, "kind": descriptor["kind"], "purpose": descriptor["purpose"],
            "path": descriptor["path"], "sha256": _digest(content),
        })
    return SealedConceptV4(source=source, images=tuple(images))


def validate_sealed_concept_v4_tree(concept: SealedConceptV4, concept_root: Path) -> None:
    root = Path(concept_root).resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise ContractError("Concept v4 image root must be a real directory")
    expected = {item["path"]: item["sha256"] for item in concept.images}
    observed: set[str] = set()
    for path in root.rglob("*"):
        identity = path.lstat()
        if path.is_symlink() or (not stat.S_ISDIR(identity.st_mode) and not stat.S_ISREG(identity.st_mode)):
            raise ContractError("Concept v4 image tree contains an unsafe entry")
        if stat.S_ISDIR(identity.st_mode):
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in expected:
            raise ContractError("Concept v4 image tree contains an unexpected file")
        if _digest(path.read_bytes()) != expected[relative]:
            raise ContractError("Concept v4 image differs from its sealed identity")
        observed.add(relative)
    if observed != set(expected):
        raise ContractError("Concept v4 image tree is incomplete")


__all__ = [
    "FIXED_OVERALL_ROLES", "FIXED_PRESENTATION_PROMPT", "FIXED_PROMPT_PROTOCOL_VERSION",
    "FIXED_VIEW_INSTRUCTIONS_KIND", "MAX_FIXED_COMPONENTS", "PRE_RENDER_CONCEPT_V4_KIND",
    "SEALED_CONCEPT_V4_KIND", "PreRenderConceptV4", "SealedConceptV4",
    "derive_fixed_roles", "fixed_prompt_protocol_sha256", "normalize_fixed_view_concept",
    "seal_pre_render_concept_v4", "validate_fixed_view_instructions",
    "validate_sealed_concept_v4_tree",
]
