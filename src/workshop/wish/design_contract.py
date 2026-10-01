"""Design Contract parsing and sealing checks (ADR 0072, Delivery 2).

A Design Contract is the Markdown file ``build-a-toy`` produces: prose plus
one fenced ``design-contract`` JSON block (see
``.claude/skills/build-a-toy/CONTRACT-FORMAT.md``). ``workshop wish
--contract`` seals the whole file, byte for byte, as the Wish objective. A
contract that fails any check here must refuse before a run starts: falling
back silently to ordinary Wish mode would recreate the defect ADR 0072
removes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from workshop.errors import ContractError

# Both limits are input guards on agent-supplied text, not design judgements
# (ADR 0072, "Limits"). The assembly limit traces to commit deed467e.
MAX_ASSEMBLY_REQUIREMENTS = 16
MAX_GEOMETRY_REQUIREMENTS = 4
# Schema 2 adds the Interfaces section (ADR 0082). Schema 1 contracts, sealed
# before it, stay valid without one.
SCHEMA_VERSIONS = (1, 2)
INTERFACES_SCHEMA_VERSION = 2
INTERFACE_KINDS = ("static", "separable", "coupled")
ENVELOPE_SHAPES = ("box", "cylinder")

_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)
_GEOMETRY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# An Interface may name one instance of a Unique Geometry whose count is
# above 1: ``wing#2`` (issue #80, ADR 0082).
_INSTANCE_REFERENCE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)#([0-9]+)$")
_REQUIREMENT_ID = re.compile(r"^R[0-9]{2}$")
_REFERENCE_FILE = re.compile(
    r"^ref-(?:0[1-9]|[1-9][0-9])-[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\.(?:png|jpg|webp)$"
)


@dataclass(frozen=True)
class ContractReference:
    file: str
    shows: str


@dataclass(frozen=True)
class ContractGeometry:
    id: str
    name: str
    count: int
    extents_mm: Tuple[float, float, float]
    wall_min_mm: float


@dataclass(frozen=True)
class ContractRequirement:
    id: str
    scope: str
    text: str


@dataclass(frozen=True)
class ContractInterface:
    """One meeting between Components (ADR 0082).

    Each Component reference is a Unique Geometry id or one instance of it,
    ``<id>#<n>`` (issue #80), kept verbatim everywhere it appears.
    ``envelope`` is the Keep-out Envelope of a separable Interface, and
    ``yielding`` with ``poses`` (an inline pose table) or ``poses_from`` (a
    motion-manifest condition id) belong to a coupled one. Each is kept as the
    exact JSON the contract sealed.
    """

    id: str
    kind: str
    components: Tuple[str, ...]
    envelope: Optional[Dict[str, Any]] = None
    yielding: Optional[str] = None
    poses: Optional[Dict[str, Any]] = None
    poses_from: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "id": self.id, "kind": self.kind, "components": list(self.components),
        }
        for key in ("envelope", "yielding", "poses", "poses_from"):
            if getattr(self, key) is not None:
                value[key] = getattr(self, key)
        return value


@dataclass(frozen=True)
class DesignContract:
    """The checkable enumeration sealed from a Design Contract's JSON block."""

    schema_version: int
    title: str
    inventor: str
    envelope_mm: Tuple[float, float, float]
    references: Tuple[ContractReference, ...]
    geometries: Tuple[ContractGeometry, ...]
    requirements: Tuple[ContractRequirement, ...]
    # None for a schema 1 contract, which has no Interfaces section.
    interfaces: Optional[Tuple[ContractInterface, ...]] = None

    def reference_labels(self) -> Dict[str, str]:
        """Sealed file name -> the label Contract Mode uses in Make round summaries."""

        return {reference.file: reference.shows for reference in self.references}

    def check_reference_names(self, names: Sequence[str]) -> None:
        """Refuse reference images that would not reach their contract labels.

        Make labels a sealed image by looking its file name up in
        ``reference_labels`` (ADR 0072), so an image sealed under any other
        name is scored as nothing, and a run given no image scores nothing at
        all. The images must seal as exactly the files this contract lists, in
        its order; every mismatch is named at once.
        """

        expected = [reference.file for reference in self.references]
        errors: List[str] = []
        if len(names) != len(expected):
            errors.append(
                "it lists %d reference image(s) but %d were given"
                % (len(expected), len(names))
            )
        for position, (given, listed) in enumerate(zip(names, expected), start=1):
            if given != listed:
                errors.append(
                    "reference image %d seals as %s, not %s" % (position, given, listed)
                )
        if errors:
            raise ContractError(
                "design contract: %s; pass the contract's images under its file "
                "names and in its order" % "; ".join(errors)
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "title": self.title,
            "inventor": self.inventor,
            "envelope_mm": list(self.envelope_mm),
            "references": [
                {"file": item.file, "shows": item.shows} for item in self.references
            ],
            "geometries": [
                {
                    "id": item.id,
                    "name": item.name,
                    "count": item.count,
                    "extents_mm": list(item.extents_mm),
                    "wall_min_mm": item.wall_min_mm,
                }
                for item in self.geometries
            ],
            "requirements": [
                {"id": item.id, "scope": item.scope, "text": item.text}
                for item in self.requirements
            ],
            **(
                {"interfaces": [item.to_dict() for item in self.interfaces]}
                if self.interfaces is not None
                else {}
            ),
        }


def _dimensions(value: Any, label: str, errors: List[str]) -> Tuple[float, float, float]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value)
        or any(item <= 0 for item in value)
    ):
        errors.append("%s must be three positive numbers" % label)
        return (0.0, 0.0, 0.0)
    return (float(value[0]), float(value[1]), float(value[2]))


def _scope(value: Any, geometry_ids: Optional[frozenset], label: str, errors: List[str]) -> Optional[str]:
    if not isinstance(value, str) or not value:
        errors.append("%s must be 'assembly' or 'geometry:<id>'" % label)
        return None
    if value == "assembly":
        return value
    if value.startswith("geometry:"):
        geometry_id = value[len("geometry:"):]
        if geometry_ids is not None and geometry_id not in geometry_ids:
            errors.append("%s cites a Unique Geometry that does not exist: %r" % (label, geometry_id))
            return None
        return value
    errors.append("%s must be 'assembly' or 'geometry:<id>'" % label)
    return None


def _parse_geometries(value: Any, errors: List[str]) -> Tuple[Tuple[ContractGeometry, ...], frozenset]:
    if not isinstance(value, list) or not value:
        errors.append("geometries must be a non-empty list")
        return (), frozenset()
    geometries: List[ContractGeometry] = []
    seen: set = set()
    for index, item in enumerate(value):
        label = "geometries[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or _GEOMETRY_ID.fullmatch(identifier) is None:
            errors.append("%s.id must be lowercase kebab case" % label)
            identifier = None
        elif identifier in seen:
            errors.append("%s.id repeats an earlier geometry id: %r" % (label, identifier))
            identifier = None
        else:
            seen.add(identifier)
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append("%s.name must be a non-empty string" % label)
        count = item.get("count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            errors.append("%s.count must be a positive integer" % label)
        extents = _dimensions(item.get("extents_mm"), "%s.extents_mm" % label, errors)
        wall_min = item.get("wall_min_mm")
        if isinstance(wall_min, bool) or not isinstance(wall_min, (int, float)) or wall_min <= 0:
            errors.append("%s.wall_min_mm must be a positive number" % label)
            wall_min = 0.0
        if identifier is not None:
            geometries.append(
                ContractGeometry(
                    id=identifier,
                    name=name if isinstance(name, str) else "",
                    count=count if isinstance(count, int) and not isinstance(count, bool) else 0,
                    extents_mm=extents,
                    wall_min_mm=float(wall_min),
                )
            )
    return tuple(geometries), frozenset(seen)


def _parse_references(
    value: Any, geometry_ids: frozenset, errors: List[str]
) -> Tuple[ContractReference, ...]:
    if not isinstance(value, list) or not value:
        errors.append("references must be a non-empty list")
        return ()
    references: List[ContractReference] = []
    for index, item in enumerate(value):
        label = "references[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        file_name = item.get("file")
        if not isinstance(file_name, str) or _REFERENCE_FILE.fullmatch(file_name) is None:
            errors.append("%s.file must look like ref-NN-<slug>.png, .jpg, or .webp" % label)
            file_name = None
        shows = _scope(item.get("shows"), geometry_ids, "%s.shows" % label, errors)
        if file_name is not None and shows is not None:
            references.append(ContractReference(file=file_name, shows=shows))
    return tuple(references)


def _parse_requirements(
    value: Any, geometry_ids: frozenset, errors: List[str]
) -> Tuple[ContractRequirement, ...]:
    if not isinstance(value, list) or not value:
        errors.append("requirements must be a non-empty list")
        return ()
    requirements: List[ContractRequirement] = []
    seen: set = set()
    for index, item in enumerate(value):
        label = "requirements[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or _REQUIREMENT_ID.fullmatch(identifier) is None:
            errors.append("%s.id must look like R01" % label)
            identifier = None
        elif identifier in seen:
            errors.append("%s.id repeats an earlier requirement id: %r" % (label, identifier))
            identifier = None
        else:
            seen.add(identifier)
        scope = _scope(item.get("scope"), geometry_ids, "%s.scope" % label, errors)
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append("%s.text must be a non-empty string" % label)
            text = None
        if identifier is not None and scope is not None and text is not None:
            requirements.append(ContractRequirement(id=identifier, scope=scope, text=text))
    return tuple(requirements)


def _number_list(value: Any, length: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) == length
        and all(not isinstance(item, bool) and isinstance(item, (int, float)) for item in value)
    )


def _envelope_shape(item: Any, label: str, errors: List[str]) -> None:
    """One simple solid of a Keep-out Envelope, in assembly coordinates."""

    if not isinstance(item, dict):
        errors.append("%s must be an object" % label)
        return
    pose = item.get("pose")
    if not isinstance(pose, str) or _GEOMETRY_ID.fullmatch(pose) is None:
        errors.append("%s.pose must be a lowercase kebab-case pose name" % label)
    kinds = [kind for kind in ENVELOPE_SHAPES if kind in item]
    if len(kinds) != 1 or set(item) != {"pose", kinds[0]}:
        errors.append("%s must hold its pose and exactly one of box or cylinder" % label)
        return
    shape = item[kinds[0]]
    if kinds[0] == "box":
        if (
            not isinstance(shape, dict)
            or set(shape) != {"min_mm", "max_mm"}
            or not _number_list(shape["min_mm"], 3)
            or not _number_list(shape["max_mm"], 3)
            or any(low >= high for low, high in zip(shape["min_mm"], shape["max_mm"]))
        ):
            errors.append("%s.box needs min_mm and max_mm, three numbers each, min below max" % label)
        return
    if (
        not isinstance(shape, dict)
        or set(shape) != {"base_mm", "axis", "radius_mm", "height_mm"}
        or not _number_list(shape["base_mm"], 3)
        or not _number_list(shape["axis"], 3)
        or not any(shape["axis"])
        or any(
            isinstance(shape[key], bool) or not isinstance(shape[key], (int, float)) or shape[key] <= 0
            for key in ("radius_mm", "height_mm")
        )
    ):
        errors.append(
            "%s.cylinder needs base_mm and a non-zero axis (three numbers each) and a "
            "positive radius_mm and height_mm" % label
        )


def _parse_envelope(value: Any, components: Sequence[str], label: str, errors: List[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"inside", "outside", "shapes"}:
        errors.append("%s needs a Keep-out Envelope: inside, outside and shapes" % label)
        return
    inside, outside = value["inside"], value["outside"]
    if inside not in components or outside not in components or inside == outside:
        errors.append("%s.inside and .outside must be two different Components it joins" % label)
    shapes = value["shapes"]
    if not isinstance(shapes, list) or not shapes:
        errors.append("%s.shapes must list one shape, or one per declared pose" % label)
        return
    for index, item in enumerate(shapes):
        _envelope_shape(item, "%s.shapes[%d]" % (label, index), errors)
    poses = [item.get("pose") for item in shapes if isinstance(item, dict)]
    if len(set(poses)) != len(poses):
        errors.append("%s.shapes name a pose more than once" % label)


def _parse_poses(value: Any, components: Sequence[str], label: str, errors: List[str]) -> None:
    """A coupled Interface's pose table, in check_motion's mover form."""

    if not isinstance(value, dict) or set(value) != {"steps", "movers"}:
        errors.append("%s needs steps and movers" % label)
        return
    steps = value["steps"]
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        errors.append("%s.steps must be a positive integer" % label)
    movers = value["movers"]
    if not isinstance(movers, list) or not movers:
        errors.append("%s.movers must be a non-empty list" % label)
        return
    seen: set = set()
    for index, mover in enumerate(movers):
        where = "%s.movers[%d]" % (label, index)
        if not isinstance(mover, dict) or not set(mover) <= {"component", "rotation", "translation", "driven"}:
            errors.append("%s may hold only component, rotation, translation and driven" % where)
            continue
        component = mover.get("component")
        if component not in components:
            errors.append("%s.component must be a Component the Interface joins" % where)
        elif component in seen:
            errors.append("%s repeats the mover %r" % (where, component))
        else:
            seen.add(component)
        if not any(isinstance(mover.get(key), dict) and mover[key] for key in ("rotation", "translation")):
            errors.append("%s needs a rotation, a translation, or both" % where)
        if "driven" in mover and not isinstance(mover["driven"], bool):
            errors.append("%s.driven must be true or false" % where)


def interface_geometry(reference: str) -> str:
    """The Unique Geometry id an Interface Component reference names:
    ``wing`` for both ``wing`` and ``wing#2``."""

    match = _INSTANCE_REFERENCE.fullmatch(reference)
    return match.group(1) if match is not None else reference


def _check_component_reference(entry: str, counts: Dict[str, int], label: str, errors: List[str]) -> None:
    """One Interface Component reference: a Unique Geometry id, or
    ``<id>#<n>`` for one instance of a geometry whose count is above 1."""

    match = _INSTANCE_REFERENCE.fullmatch(entry)
    geometry = match.group(1) if match is not None else entry
    if geometry not in counts:
        errors.append("%s.components cites a Unique Geometry that does not exist: %r" % (label, entry))
        return
    if match is None:
        return
    count, number = counts[geometry], match.group(2)
    if count < 2:
        errors.append(
            "%s.components names instance %r, but %r has count %d; name the Unique Geometry itself"
            % (label, entry, geometry, count)
        )
    elif number != str(int(number)) or not 1 <= int(number) <= count:
        errors.append(
            "%s.components names instance %r; %r has instances #1 to #%d" % (label, entry, geometry, count)
        )


def _parse_interfaces(
    value: Any, counts: Dict[str, int], errors: List[str]
) -> Tuple[ContractInterface, ...]:
    """The Interfaces section (ADR 0082): every meeting between Components,
    with its Kind and what that Kind needs. An empty list is a toy whose
    Components never meet.

    ``counts`` maps each Unique Geometry id to its count. A Component
    reference is a geometry id or one instance of it, ``<id>#<n>`` (issue
    #80); the references of one Interface are distinct, and a geometry and an
    instance of it never appear together."""

    if not isinstance(value, list):
        errors.append("interfaces must be a list (schema_version 2)")
        return ()
    interfaces: List[ContractInterface] = []
    seen: set = set()
    for index, item in enumerate(value):
        label = "interfaces[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or _GEOMETRY_ID.fullmatch(identifier) is None:
            errors.append("%s.id must be lowercase kebab case" % label)
            identifier = None
        elif identifier in seen:
            errors.append("%s.id repeats an earlier interface id: %r" % (label, identifier))
            identifier = None
        else:
            seen.add(identifier)
        kind = item.get("kind")
        if kind not in INTERFACE_KINDS:
            errors.append("%s.kind must be static, separable or coupled" % label)
            kind = None
        components = item.get("components")
        if (
            not isinstance(components, list)
            or len(components) < 2
            or not all(isinstance(entry, str) for entry in components)
            or len(set(components)) != len(components)
        ):
            errors.append("%s.components must name two or more different Components" % label)
            components = []
        else:
            for entry in components:
                _check_component_reference(entry, counts, label, errors)
            instanced = {interface_geometry(entry) for entry in components if interface_geometry(entry) != entry}
            for entry in components:
                if entry in instanced:
                    errors.append(
                        "%s.components names both %r and an instance of it; name every instance, or the "
                        "Unique Geometry alone" % (label, entry)
                    )
        allowed = {"id", "kind", "components"}
        if kind == "separable":
            allowed.add("envelope")
            _parse_envelope(item.get("envelope"), components, "%s.envelope" % label, errors)
        elif kind == "coupled":
            allowed |= {"yielding", "poses", "poses_from"}
            if item.get("yielding") not in components:
                errors.append("%s.yielding must name the Component that changes when the Interface fails" % label)
            if ("poses" in item) == ("poses_from" in item):
                errors.append("%s needs exactly one of poses (a pose table) or poses_from (its kinematic source)" % label)
            elif "poses" in item:
                _parse_poses(item["poses"], components, "%s.poses" % label, errors)
            elif not isinstance(item["poses_from"], str) or not item["poses_from"].strip():
                errors.append("%s.poses_from must name a coupled_motion_collision condition id" % label)
        extra = sorted(set(item) - allowed)
        if extra and kind is not None:
            errors.append("%s: a %s Interface does not take %s" % (label, kind, ", ".join(extra)))
        if identifier is not None and kind is not None and components:
            interfaces.append(
                ContractInterface(
                    id=identifier,
                    kind=kind,
                    components=tuple(components),
                    envelope=item.get("envelope") if kind == "separable" else None,
                    yielding=item.get("yielding") if kind == "coupled" else None,
                    poses=item.get("poses") if kind == "coupled" else None,
                    poses_from=item.get("poses_from") if kind == "coupled" else None,
                )
            )
    return tuple(interfaces)


def parse_design_contract(text: str) -> DesignContract:
    """Parse and validate the fenced ``design-contract`` block inside ``text``.

    Every failure this function can detect is collected and raised together
    in one ``ContractError`` (ADR 0072: "The refusal names every failure at
    once"). A contract that does not parse at all, or whose block is not a
    JSON object, refuses immediately -- there is nothing else to check.
    """

    match = _FENCE.search(text)
    if match is None:
        raise ContractError(
            "design contract: no fenced ```design-contract``` block was found"
        )
    try:
        block = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(
            "design contract: the design-contract block does not parse as JSON: %s" % exc
        ) from exc
    if not isinstance(block, dict):
        raise ContractError("design contract: the design-contract block must be a JSON object")

    errors: List[str] = []

    schema_version = block.get("schema_version")
    if isinstance(schema_version, bool) or schema_version not in SCHEMA_VERSIONS:
        errors.append("schema_version must be 1 or 2")

    title = block.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")

    inventor = block.get("inventor")
    if not isinstance(inventor, str) or not inventor.strip():
        errors.append("inventor must be a non-empty string")

    envelope_mm = _dimensions(block.get("envelope_mm"), "envelope_mm", errors)

    geometries, geometry_ids = _parse_geometries(block.get("geometries"), errors)
    references = _parse_references(block.get("references"), geometry_ids, errors)
    requirements = _parse_requirements(block.get("requirements"), geometry_ids, errors)
    interfaces: Optional[Tuple[ContractInterface, ...]] = None
    if schema_version == INTERFACES_SCHEMA_VERSION:
        counts = {item.id: item.count for item in geometries}
        interfaces = _parse_interfaces(block.get("interfaces"), counts, errors)
    elif "interfaces" in block:
        errors.append("interfaces need schema_version 2")

    assembly_count = sum(1 for item in requirements if item.scope == "assembly")
    if assembly_count > MAX_ASSEMBLY_REQUIREMENTS:
        errors.append(
            "at most %d assembly-scoped requirements are allowed, found %d"
            % (MAX_ASSEMBLY_REQUIREMENTS, assembly_count)
        )
    per_geometry: Dict[str, int] = {}
    for item in requirements:
        if item.scope.startswith("geometry:"):
            per_geometry[item.scope] = per_geometry.get(item.scope, 0) + 1
    for scope, count in sorted(per_geometry.items()):
        if count > MAX_GEOMETRY_REQUIREMENTS:
            errors.append(
                "at most %d requirements are allowed for %s, found %d"
                % (MAX_GEOMETRY_REQUIREMENTS, scope, count)
            )

    if errors:
        raise ContractError("design contract: " + "; ".join(errors))

    return DesignContract(
        schema_version=schema_version,
        title=title,
        inventor=inventor,
        envelope_mm=envelope_mm,
        references=references,
        geometries=geometries,
        requirements=requirements,
        interfaces=interfaces,
    )
