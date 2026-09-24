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
from typing import Any, Dict, List, Mapping, Optional, Tuple

from workshop.errors import ContractError

# Both limits are input guards on agent-supplied text, not design judgements
# (ADR 0072, "Limits"). The assembly limit traces to commit deed467e.
MAX_ASSEMBLY_REQUIREMENTS = 16
MAX_GEOMETRY_REQUIREMENTS = 4

_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)
_GEOMETRY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
class DesignContract:
    """The checkable enumeration sealed from a Design Contract's JSON block."""

    schema_version: int
    title: str
    inventor: str
    envelope_mm: Tuple[float, float, float]
    references: Tuple[ContractReference, ...]
    geometries: Tuple[ContractGeometry, ...]
    requirements: Tuple[ContractRequirement, ...]

    def reference_labels(self) -> Dict[str, str]:
        """Sealed file name -> the label Contract Mode uses in Make round summaries."""

        return {reference.file: reference.shows for reference in self.references}

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
    if isinstance(schema_version, bool) or schema_version != 1:
        errors.append("schema_version must be 1")

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
    )
