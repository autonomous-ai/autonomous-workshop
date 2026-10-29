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
from workshop.wish.assembly_tree import ContractAssemblyTree, parse_assembly_tree
from workshop.wish.catalogues import Catalogues, load_catalogues
from workshop.wish.print_sheets import ContractPrint, parse_print_section

# ADR 0072's row limits (16 assembly-scoped rows, 4 per Unique Geometry) are
# gone (ADR 0093 decision 6): a kit writes one row per Part for what can be
# seen. The file itself stays bounded by the Wish objective limit.
# Schema 2 adds the Interfaces section (ADR 0082). Schema 1 contracts, sealed
# before it, stay valid without one. Schema 3 keeps the Interfaces and gives
# every reference its Reference Camera (ADR 0083). Schema 4 keeps both and
# gives every Interface the text of what it imposes on each Component it
# joins (ADR 0084). Schema 5 keeps all three and adds Guide Images, which
# explain the design and are never compared with the model (ADR 0089).
# Schema 6 keeps all four, makes Guide Images optional, and requires the
# Print Sheets section (ADR 0091). Schema 7 keeps all five, makes the Print
# Sheets optional, and requires the Assembly Tree that splits the toy into
# kit Parts (ADR 0092). Schema 8 keeps all six, makes the Assembly Tree
# optional again (a kit has one, any other toy has none), and requires what
# ADR 0093 adds: every Unique Geometry names the prose ``###`` sections that
# describe it (``prose_sections``), which Make delivers to its Component
# Worker, and every Unique Geometry is named by at least one Guide Image, the
# two extra views of its three-view sheet. Schema 9 is schema 8 without
# ``wall_min_mm`` (ADR 0094): Make gates every wall at the nozzle's print
# minimum and never measured a per-geometry floor, so a schema 9 geometry
# states none and refuses one.
SCHEMA_VERSIONS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
INTERFACES_SCHEMA_VERSION = 2
CAMERA_SCHEMA_VERSION = 3
INTERFACE_TEXT_SCHEMA_VERSION = 4
GUIDE_SCHEMA_VERSION = 5
PRINT_SCHEMA_VERSION = 6
TREE_SCHEMA_VERSION = 7
PROSE_SCHEMA_VERSION = 8
NO_WALL_SCHEMA_VERSION = 9
# A run may seal these. Schema 7 became sealable once every gate it needs was
# wired: Make's tree gates (ADR 0092 decision 8, issue #136) and its Manual
# (decision 9, issue #137), which the host checks before Make is accepted.
SEALABLE_SCHEMA_VERSIONS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
MAX_GUIDE_SHOWS_CHARS = 500
MAX_GUIDE_STEPS = 24
MAX_GUIDE_STEP_CHARS = 300
# A Reference Camera, in degrees, in render_review's convention: azimuth 0
# looks from +X, -90 from the front (-Y); elevation 90 looks down from above.
CAMERA_AZIMUTH_RANGE = (-180.0, 180.0)
CAMERA_ELEVATION_RANGE = (-90.0, 90.0)
INTERFACE_KINDS = ("static", "separable", "coupled")
ENVELOPE_SHAPES = ("box", "cylinder")

_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)
_GEOMETRY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# An Interface may name one instance of a Unique Geometry whose count is
# above 1: ``wing#2`` (issue #80, ADR 0082).
_INSTANCE_REFERENCE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)#([0-9]+)$")
# R01..R99, then R100..R999: with no row limit (ADR 0093) a kit may pass 99 rows.
_REQUIREMENT_ID = re.compile(r"^R(?:[0-9]{2}|[1-9][0-9]{2})$")
_REFERENCE_FILE = re.compile(
    r"^ref-(?:0[1-9]|[1-9][0-9]{1,2})-[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\.(?:png|jpg|webp)$"
)
_GUIDE_FILE = re.compile(
    r"^guide-(?:0[1-9]|[1-9][0-9]{1,2})-[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\.(?:png|jpg|webp)$"
)
# An ATX heading of the contract's prose (ADR 0093), and a line opening or
# closing a fenced block, inside which no line is a heading.
_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
_FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_CONTRACT_FENCE_OPEN = re.compile(r"^ {0,3}```design-contract\s*$")


@dataclass(frozen=True)
class ContractReference:
    file: str
    shows: str
    # The Reference Camera ``(azimuth, elevation)`` in degrees, in the Display
    # Pose frame (ADR 0083). Required from schema 3, absent before it.
    camera: Optional[Tuple[float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {"file": self.file, "shows": self.shows}
        if self.camera is not None:
            value["camera"] = [_plain_number(item) for item in self.camera]
        return value


def _plain_number(value: float) -> Any:
    """An integral camera angle seals as an integer, as the contract wrote it."""

    return int(value) if float(value).is_integer() else value


@dataclass(frozen=True)
class ContractGuide:
    """One Guide Image (ADR 0089): sealed with the contract to explain the
    design, read by the Manager and Component Workers, and never scored or
    compared with the model. ``shows`` says what it explains; ``steps``,
    when given, names each step it draws, in order, so the run can account
    for every one. ``geometries``, when given, names the Unique Geometries
    whose Component Workers read it (issue #125); without it every
    Component Worker does."""

    file: str
    shows: str
    steps: Tuple[str, ...] = ()
    geometries: Optional[Tuple[str, ...]] = None

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {"file": self.file, "shows": self.shows}
        if self.steps:
            value["steps"] = list(self.steps)
        if self.geometries is not None:
            value["geometries"] = list(self.geometries)
        return value


@dataclass(frozen=True)
class ContractGeometry:
    id: str
    name: str
    count: int
    extents_mm: Tuple[float, float, float]
    # The geometry's minimum wall before schema 9; None from schema 9 on,
    # which states none (ADR 0094).
    wall_min_mm: Optional[float]
    # The exact ``###`` heading texts of the prose sections that describe this
    # geometry (schema 8, ADR 0093); None before schema 8.
    prose_sections: Optional[Tuple[str, ...]] = None

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "count": self.count,
            "extents_mm": list(self.extents_mm),
        }
        if self.wall_min_mm is not None:
            value["wall_min_mm"] = self.wall_min_mm
        if self.prose_sections is not None:
            value["prose_sections"] = list(self.prose_sections)
        return value


@dataclass(frozen=True)
class ContractProseSection:
    """One prose ``###`` section a schema 8 geometry names (ADR 0093): its
    exact heading text and the text from the line after the heading to the
    next heading of level 3 or above, outside the design-contract block.
    Sealed inside the contract so Make delivers it to the Component Worker."""

    heading: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"heading": self.heading, "text": self.text}


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
    exact JSON the contract sealed. ``text`` (schema 4, ADR 0084) states in
    words what the Interface imposes on each Component it joins; it informs
    the reviewer and the worker, and no gate measures it.
    """

    id: str
    kind: str
    components: Tuple[str, ...]
    envelope: Optional[Dict[str, Any]] = None
    yielding: Optional[str] = None
    poses: Optional[Dict[str, Any]] = None
    poses_from: Optional[str] = None
    text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "id": self.id, "kind": self.kind, "components": list(self.components),
        }
        for key in ("envelope", "yielding", "poses", "poses_from", "text"):
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
    # None before schema 5, which has no Guide Images (ADR 0089), and for a
    # schema 6 contract that lists none.
    guides: Optional[Tuple[ContractGuide, ...]] = None
    # None before schema 6, which has no Print Sheets (ADR 0091), and for a
    # schema 7 contract that has none.
    print_sheets: Optional[ContractPrint] = None
    # None before schema 7, which has no Assembly Tree (ADR 0092), and for a
    # schema 8 contract that is not a kit.
    assembly_tree: Optional[ContractAssemblyTree] = None
    # Schema 8 (ADR 0093): every prose section some geometry names, in the
    # order the prose gives them. None before schema 8.
    prose: Optional[Tuple[ContractProseSection, ...]] = None

    def check_sealable(self) -> None:
        """Refuse a contract no run can seal yet (schema 7: see
        ``SEALABLE_SCHEMA_VERSIONS``)."""

        if self.schema_version not in SEALABLE_SCHEMA_VERSIONS:
            raise ContractError(
                "design contract: schema_version %d is validated, but no run can seal it yet"
                % self.schema_version
            )

    def kit_catalogue(self) -> Optional[Dict[str, Any]]:
        """The catalogue entries a schema 7 or 8 tree uses, sealed beside the
        contract (ADR 0092) so Make's tree gates read the colour of each
        printed Part and the size of each Bought Part from the Wish, not from
        whatever the owner's catalogue says later. None before schema 7."""

        return None if self.assembly_tree is None else self.assembly_tree.catalogue_snapshot()

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

    def check_guide_names(self, names: Sequence[str]) -> None:
        """Refuse Guide Images that would not seal as this contract's guides.

        The same rule as ``check_reference_names`` (ADR 0089): exactly the
        files ``guides[]`` lists, in its order. A contract before schema 5
        takes no Guide Image at all.
        """

        expected = [guide.file for guide in self.guides or ()]
        errors: List[str] = []
        if len(names) != len(expected):
            errors.append(
                "it lists %d guide image(s) but %d were given" % (len(expected), len(names))
            )
        for position, (given, listed) in enumerate(zip(names, expected), start=1):
            if given != listed:
                errors.append("guide image %d seals as %s, not %s" % (position, given, listed))
        if errors:
            raise ContractError(
                "design contract: %s; pass the contract's guide images with --guide, "
                "under its file names and in its order" % "; ".join(errors)
            )

    def check_print_art_names(self, names: Sequence[str]) -> None:
        """Refuse print art that would not seal as this contract's art.

        The same rule as ``check_reference_names`` (ADR 0091): exactly the
        files ``print.art`` lists, in its order. A contract before schema 6
        takes no print art at all.
        """

        expected = list(self.print_sheets.art_files) if self.print_sheets is not None else []
        errors: List[str] = []
        if len(names) != len(expected):
            errors.append(
                "it lists %d print art image(s) but %d were given" % (len(expected), len(names))
            )
        for position, (given, listed) in enumerate(zip(names, expected), start=1):
            if given != listed:
                errors.append("print art %d seals as %s, not %s" % (position, given, listed))
        if errors:
            raise ContractError(
                "design contract: %s; pass the contract's print art with --print-art, "
                "under its file names and in its order" % "; ".join(errors)
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "title": self.title,
            "inventor": self.inventor,
            "envelope_mm": list(self.envelope_mm),
            "references": [item.to_dict() for item in self.references],
            "geometries": [item.to_dict() for item in self.geometries],
            "requirements": [
                {"id": item.id, "scope": item.scope, "text": item.text}
                for item in self.requirements
            ],
            **(
                {"interfaces": [item.to_dict() for item in self.interfaces]}
                if self.interfaces is not None
                else {}
            ),
            **(
                {"guides": [item.to_dict() for item in self.guides]}
                if self.guides is not None
                else {}
            ),
            **(
                {"print": self.print_sheets.to_dict()}
                if self.print_sheets is not None
                else {}
            ),
            **(
                {"assembly_tree": self.assembly_tree.to_dict()}
                if self.assembly_tree is not None
                else {}
            ),
            **(
                {"prose": [item.to_dict() for item in self.prose]}
                if self.prose is not None
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


def _parse_geometries(
    value: Any, errors: List[str], prose: bool = False, wall: bool = True
) -> Tuple[Tuple[ContractGeometry, ...], frozenset]:
    """The Unique Geometries; ``prose`` (schema 8) requires each one's
    ``prose_sections``, and before schema 8 the field is refused rather than
    ignored. ``wall`` (before schema 9) requires each one's ``wall_min_mm``;
    from schema 9 on it is refused (ADR 0094)."""

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
        if not wall:
            if "wall_min_mm" in item:
                errors.append(
                    "%s.wall_min_mm is not part of schema_version 9: Make gates every "
                    "wall at the nozzle's print minimum (ADR 0094)" % label
                )
            wall_min = None
        elif isinstance(wall_min, bool) or not isinstance(wall_min, (int, float)) or wall_min <= 0:
            errors.append("%s.wall_min_mm must be a positive number" % label)
            wall_min = 0.0
        sections: Optional[Tuple[str, ...]] = None
        if prose:
            raw = item.get("prose_sections")
            if (
                not isinstance(raw, list) or not raw
                or any(not isinstance(entry, str) or not entry.strip() for entry in raw)
            ):
                errors.append(
                    "%s.prose_sections must name at least one prose ### heading "
                    "(schema_version 8)" % label
                )
            elif len(set(raw)) != len(raw):
                errors.append("%s.prose_sections names a heading twice" % label)
            else:
                sections = tuple(raw)
        elif "prose_sections" in item:
            errors.append("%s.prose_sections needs schema_version 8" % label)
        if identifier is not None:
            geometries.append(
                ContractGeometry(
                    id=identifier,
                    name=name if isinstance(name, str) else "",
                    count=count if isinstance(count, int) and not isinstance(count, bool) else 0,
                    extents_mm=extents,
                    wall_min_mm=None if wall_min is None else float(wall_min),
                    prose_sections=sections,
                )
            )
    return tuple(geometries), frozenset(seen)


def prose_sections(text: str) -> List[Tuple[int, str, str]]:
    """``(level, heading, text)`` of every ATX heading of a contract file's
    prose, in order (ADR 0093). A line inside a fenced block is never a
    heading, and the design-contract block belongs to no section. A
    section's text runs from the line after its heading to the next heading
    of level 3 or above, without surrounding blank lines."""

    found: List[Tuple[int, str, List[str]]] = []
    fence: Optional[str] = None
    in_contract = False
    for line in text.splitlines():
        marker = _FENCE_LINE.match(line)
        if fence is not None:
            closes = (
                marker is not None
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
                and not line.strip()[len(marker.group(1)):].strip()
            )
            if closes:
                fence = None
            if in_contract:
                in_contract = not closes
            elif found:
                found[-1][2].append(line)
            continue
        if marker is not None:
            fence = marker.group(1)
            if _CONTRACT_FENCE_OPEN.match(line):
                in_contract = True
            elif found:
                found[-1][2].append(line)
            continue
        heading = _HEADING.match(line)
        if heading is not None and len(heading.group(1)) <= 3:
            found.append((len(heading.group(1)), heading.group(2), []))
            continue
        if found:
            found[-1][2].append(line)
    return [(level, heading, "\n".join(body).strip("\n").rstrip()) for level, heading, body in found]


def _parse_prose(
    text: str, geometries: Sequence[ContractGeometry], errors: List[str]
) -> Tuple[ContractProseSection, ...]:
    """Schema 8's prose sections (ADR 0093): each heading a geometry names is
    exactly one ``###`` heading of the prose and has text; one section may
    serve several geometries. Returned once each, in prose order."""

    sections = prose_sections(text)
    level_three: Dict[str, List[str]] = {}
    for level, heading, body in sections:
        if level == 3:
            level_three.setdefault(heading, []).append(body)
    named: set = set()
    for geometry in geometries:
        for heading in geometry.prose_sections or ():
            found = level_three.get(heading, [])
            if not found:
                errors.append(
                    "geometry %r names prose section %r, which is not a ### heading of the prose"
                    % (geometry.id, heading)
                )
            elif len(found) > 1:
                errors.append(
                    "geometry %r names prose section %r, which is a ### heading %d times"
                    % (geometry.id, heading, len(found))
                )
            elif not found[0].strip():
                errors.append("prose section %r has no text" % heading)
            else:
                named.add(heading)
    ordered: List[ContractProseSection] = []
    for level, heading, body in sections:
        if level == 3 and heading in named:
            ordered.append(ContractProseSection(heading=heading, text=body))
    return tuple(ordered)


def reference_camera(value: Any) -> Optional[Tuple[float, float]]:
    """``(azimuth, elevation)`` when ``value`` is a usable Reference Camera,
    else None: two numbers, azimuth in -180..180 and elevation in -90..90."""

    if not _number_list(value, 2):
        return None
    azimuth, elevation = float(value[0]), float(value[1])
    if not (CAMERA_AZIMUTH_RANGE[0] <= azimuth <= CAMERA_AZIMUTH_RANGE[1]):
        return None
    if not (CAMERA_ELEVATION_RANGE[0] <= elevation <= CAMERA_ELEVATION_RANGE[1]):
        return None
    return azimuth, elevation


def _parse_references(
    value: Any, geometry_ids: frozenset, errors: List[str], cameras: bool = False
) -> Tuple[ContractReference, ...]:
    """The references; ``cameras`` (schema 3) requires each one's Reference
    Camera, and before schema 3 a camera is refused rather than ignored."""

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
        camera = None
        if cameras:
            camera = reference_camera(item.get("camera"))
            if camera is None:
                errors.append(
                    "%s.camera must be [AZ, EL] in degrees, AZ in -180..180 and EL in -90..90 "
                    "(schema_version 3 or later)" % label
                )
        elif "camera" in item:
            errors.append("%s.camera needs schema_version 3 or later" % label)
        if file_name is not None and shows is not None and (camera is not None or not cameras):
            references.append(ContractReference(file=file_name, shows=shows, camera=camera))
    return tuple(references)


def _parse_guides(
    value: Any, geometry_ids: frozenset, errors: List[str]
) -> Tuple[ContractGuide, ...]:
    """Schema 5's Guide Images (ADR 0089): a non-empty list, each a
    ``guide-NN-<slug>`` file numbered from 01 in order, what it shows,
    optionally the steps it draws, and optionally the Unique Geometries
    whose Component Workers read it (issue #125)."""

    if not isinstance(value, list) or not value:
        errors.append("guides must be a non-empty list (schema_version 5)")
        return ()
    guides: List[ContractGuide] = []
    for index, item in enumerate(value):
        label = "guides[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        unknown = sorted(set(item) - {"file", "shows", "steps", "geometries"})
        if unknown:
            errors.append("%s has unknown field(s): %s" % (label, ", ".join(unknown)))
        file_name = item.get("file")
        if not isinstance(file_name, str) or _GUIDE_FILE.fullmatch(file_name) is None:
            errors.append("%s.file must look like guide-NN-<slug>.png, .jpg, or .webp" % label)
            file_name = None
        elif int(file_name.split("-")[1]) != index + 1:
            errors.append("%s.file must be numbered guide-%02d" % (label, index + 1))
            file_name = None
        shows = item.get("shows")
        if not isinstance(shows, str) or not shows.strip() or len(shows) > MAX_GUIDE_SHOWS_CHARS:
            errors.append(
                "%s.shows must say in at most %d characters what the image explains"
                % (label, MAX_GUIDE_SHOWS_CHARS)
            )
            shows = None
        steps: Tuple[str, ...] = ()
        if "steps" in item:
            raw = item["steps"]
            if (
                not isinstance(raw, list) or not 1 <= len(raw) <= MAX_GUIDE_STEPS
                or any(
                    not isinstance(step, str) or not step.strip() or len(step) > MAX_GUIDE_STEP_CHARS
                    for step in raw
                )
                or len(set(raw)) != len(raw)
            ):
                errors.append(
                    "%s.steps must be 1 to %d distinct non-empty strings of at most %d characters"
                    % (label, MAX_GUIDE_STEPS, MAX_GUIDE_STEP_CHARS)
                )
                shows = None
            else:
                steps = tuple(raw)
        geometries: Optional[Tuple[str, ...]] = None
        if "geometries" in item:
            raw = item["geometries"]
            if (
                not isinstance(raw, list) or not raw
                or any(not isinstance(entry, str) for entry in raw)
            ):
                errors.append(
                    "%s.geometries must be a non-empty list of Unique Geometry ids" % label
                )
                shows = None
            elif len(set(raw)) != len(raw):
                errors.append("%s.geometries names a Unique Geometry twice" % label)
                shows = None
            else:
                missing = [entry for entry in raw if entry not in geometry_ids]
                if missing:
                    errors.append(
                        "%s.geometries names a Unique Geometry that does not exist: %s"
                        % (label, ", ".join(repr(entry) for entry in missing))
                    )
                    shows = None
                else:
                    geometries = tuple(raw)
        if file_name is not None and shows is not None:
            guides.append(
                ContractGuide(file=file_name, shows=shows, steps=steps, geometries=geometries)
            )
    return tuple(guides)


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
    value: Any, counts: Dict[str, int], errors: List[str], text: bool = False
) -> Tuple[ContractInterface, ...]:
    """The Interfaces section (ADR 0082): every meeting between Components,
    with its Kind and what that Kind needs. An empty list is a toy whose
    Components never meet.

    ``counts`` maps each Unique Geometry id to its count. A Component
    reference is a geometry id or one instance of it, ``<id>#<n>`` (issue
    #80); the references of one Interface are distinct, and a geometry and an
    instance of it never appear together. ``text`` (schema 4) requires each
    Interface's non-empty ``text``; before schema 4 it is refused."""

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
        statement = item.get("text")
        if text:
            allowed.add("text")
            if not isinstance(statement, str) or not statement.strip():
                errors.append(
                    "%s.text must state, in words, what the Interface imposes on each Component it "
                    "joins (schema_version 4)" % label
                )
                statement = None
        elif "text" in item:
            errors.append("%s.text needs schema_version 4" % label)
            statement = None
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
        extra = [key for key in extra if key != "text"]
        if extra and kind is not None:
            errors.append("%s: a %s Interface does not take %s" % (label, kind, ", ".join(extra)))
        if identifier is not None and kind is not None and components and (statement is not None or not text):
            interfaces.append(
                ContractInterface(
                    id=identifier,
                    kind=kind,
                    components=tuple(components),
                    envelope=item.get("envelope") if kind == "separable" else None,
                    yielding=item.get("yielding") if kind == "coupled" else None,
                    poses=item.get("poses") if kind == "coupled" else None,
                    poses_from=item.get("poses_from") if kind == "coupled" else None,
                    text=statement if text else None,
                )
            )
    return tuple(interfaces)


def parse_design_contract(text: str, catalogues: Optional[Catalogues] = None) -> DesignContract:
    """Parse and validate the fenced ``design-contract`` block inside ``text``.

    A contract's Assembly Tree (schema 7, or a schema 8 kit) has its Parts
    checked against ``catalogues``, the owner's filament and Bought Part
    catalogues (ADR 0092); without it the packaged catalogues are read. A
    contract without a tree never reads them.

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
        errors.append("schema_version must be 1, 2, 3, 4, 5, 6, 7, 8 or 9")
    # Each feature below starts at one schema and carries into every later
    # one; an unknown schema reads as none of them.
    version = (
        schema_version
        if not isinstance(schema_version, bool) and schema_version in SCHEMA_VERSIONS
        else 0
    )

    title = block.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")

    inventor = block.get("inventor")
    if not isinstance(inventor, str) or not inventor.strip():
        errors.append("inventor must be a non-empty string")

    envelope_mm = _dimensions(block.get("envelope_mm"), "envelope_mm", errors)

    geometries, geometry_ids = _parse_geometries(
        block.get("geometries"), errors, prose=version >= PROSE_SCHEMA_VERSION,
        wall=version < NO_WALL_SCHEMA_VERSION,
    )
    references = _parse_references(
        block.get("references"), geometry_ids, errors,
        cameras=version >= CAMERA_SCHEMA_VERSION,
    )
    requirements = _parse_requirements(block.get("requirements"), geometry_ids, errors)
    interfaces: Optional[Tuple[ContractInterface, ...]] = None
    counts = {item.id: item.count for item in geometries}
    if version >= INTERFACES_SCHEMA_VERSION:
        interfaces = _parse_interfaces(
            block.get("interfaces"), counts, errors,
            text=version >= INTERFACE_TEXT_SCHEMA_VERSION,
        )
    elif "interfaces" in block:
        errors.append("interfaces need schema_version 2 or later")
    guides: Optional[Tuple[ContractGuide, ...]] = None
    # Guide Images: required at schema 5, optional at 6 and 7, required from
    # 8 on, where every Unique Geometry is named by one (ADR 0093 decision 5).
    if version == GUIDE_SCHEMA_VERSION or version >= PROSE_SCHEMA_VERSION or (
        version > GUIDE_SCHEMA_VERSION and "guides" in block
    ):
        guides = _parse_guides(block.get("guides"), geometry_ids, errors)
        if version >= PROSE_SCHEMA_VERSION:
            guided = {entry for guide in guides for entry in guide.geometries or ()}
            for geometry in geometries:
                if geometry.id not in guided:
                    errors.append(
                        "geometry %r is named by no guides[] entry's geometries; under "
                        "schema_version 8 or later every Unique Geometry has Guide Images" % geometry.id
                    )
    elif "guides" in block:
        errors.append("guides need schema_version 5 or later")
    # The Assembly Tree: required at schema 7, optional at 8 (a kit has one).
    kit = version == TREE_SCHEMA_VERSION or (
        version > TREE_SCHEMA_VERSION and "assembly_tree" in block
    )
    print_sheets: Optional[ContractPrint] = None
    if version == PRINT_SCHEMA_VERSION:
        print_sheets = parse_print_section(block.get("print"), counts, errors)
    elif version > PRINT_SCHEMA_VERSION and "print" in block:
        print_sheets = parse_print_section(block.get("print"), counts, errors, tree=kit)
    elif "print" in block:
        errors.append("print needs schema_version 6 or later")
    assembly_tree: Optional[ContractAssemblyTree] = None
    if kit:
        pieces = ()
        if isinstance(block.get("print"), dict) and isinstance(block["print"].get("pieces"), list):
            pieces = tuple(item for item in block["print"]["pieces"] if isinstance(item, dict))
        if catalogues is None:
            try:
                catalogues = load_catalogues()
            except ContractError as exc:
                errors.append(str(exc))
        if catalogues is not None:
            assembly_tree = parse_assembly_tree(
                block.get("assembly_tree"), counts, pieces, catalogues, errors
            )
    elif "assembly_tree" in block:
        errors.append("assembly_tree needs schema_version 7 or later")
    prose: Optional[Tuple[ContractProseSection, ...]] = None
    if version >= PROSE_SCHEMA_VERSION:
        prose = _parse_prose(text, geometries, errors)

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
        guides=guides,
        print_sheets=print_sheets,
        assembly_tree=assembly_tree,
        prose=prose,
    )
