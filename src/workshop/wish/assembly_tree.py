"""A schema 7 Design Contract's Assembly Tree (ADR 0092).

The ``assembly_tree`` section declares how the toy's Parts become the
finished toy, as a Rolife-style kit: its Parts (printed bodies, each in one
catalogued filament, and catalogued Bought Parts), its Assembly Steps in
Manual order, the Components as chosen subtrees, and the tools and
consumables the Manual lists. Print Pieces are the ``print`` section's
pieces and are leaves of the same tree.

Every check here reads only the contract and the owner's catalogues; the
gates that compare the tree with the built STEP (reconciliation, insertion
and lead-route sweeps) belong to Make (ADR 0092 decision 8). Like the rest
of the contract, parsing collects every failure instead of stopping at the
first.

The shape, in brief::

    "assembly_tree": {
      "parts": [{"id": "C01-hat", "name": "Pointed hat", "filament": "black"},
                {"id": "P01-steel-pin", "bought": "steel-pin-1.5x29.5"}],
      "steps": [{"id": "S01-desk-items", "output": "Teacher's desk, dressed",
                 "count": 1, "joint": "peg-socket",
                 "inputs": [{"id": "A01-desk"},
                            {"id": "C01-hat", "direction": [0, 0, -1]}],
                 "text": "Press the hat into the desk's socket."}],
      "components": [{"geometry": "teacher-desk", "parts": ["A01-desk", "C01-hat"]}],
      "materials": ["tweezers"]
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from workshop.wish.catalogues import Catalogues

# Joints that join inputs (ADR 0092 decision 6). Glue is a last resort and
# names its reason.
JOINS = ("peg-socket", "tab-slot", "pin-hinge", "foam-tape", "glue")
# A step that applies a Print Piece to its host.
PAPER = "paper"
# One-input steps: the input is reshaped, not joined (ADR 0092 decision 2).
SHAPINGS = ("fold", "cut", "bend", "roll")
# A step that joins LED leads (ADR 0092 decision 2).
LEADS = "leads"
JOINTS = JOINS + (PAPER,) + SHAPINGS + (LEADS,)
# Printed Part letters, grouped by filament colour (ADR 0092 decision 6).
PRINTED_LETTERS = "ABCDEFGHIJK"
MAX_COUNT = 99
MAX_TEXT_CHARS = 200
MAX_OUTPUT_CHARS = 80
MAX_NAME_CHARS = 80
MAX_REASON_CHARS = 300
MAX_EXIT_CHARS = 200
MAX_STEPS = 999

_SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
PART_ID = re.compile(r"^([A-KP])([0-9]{2})-(%s)$" % _SLUG)
STEP_ID = re.compile(r"^S([0-9]{2})-(%s)$" % _SLUG)
PIECE_ID = re.compile(r"^([MN])([0-9]{2})-(%s)$" % _SLUG)


@dataclass(frozen=True)
class ContractAssemblyTree:
    """The validated ``assembly_tree`` section, kept as the exact JSON the
    contract sealed. ``component_of`` maps every printed and Bought Part to
    the Unique Geometry of its Component; ``unconfirmed`` names the catalogue
    entries the tree uses that the owner has not confirmed."""

    section: Dict[str, Any]
    component_of: Mapping[str, str] = field(default_factory=dict)
    unconfirmed: Tuple[str, ...] = ()

    @property
    def root(self) -> str:
        return self.section["steps"][-1]["id"]

    def to_dict(self) -> Dict[str, Any]:
        return self.section


def _mnemonic(identifier: str) -> str:
    return identifier.split("-", 1)[1]


def _code(identifier: str) -> str:
    return identifier.split("-", 1)[0]


def _integer(value: Any, low: int, high: int) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and low <= value <= high


def _text(value: Any, limit: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _vector(value: Any) -> bool:
    return (
        isinstance(value, list) and len(value) == 3
        and all(not isinstance(item, bool) and isinstance(item, (int, float)) for item in value)
        and any(value)
    )


class _Ids:
    """Every id the tree and the print section declare: a duplicate id, code
    or mnemonic is refused wherever it first repeats."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        self.codes: Dict[str, str] = {}
        self.mnemonics: Dict[str, str] = {}

    def add(self, identifier: str, label: str) -> bool:
        code, mnemonic = _code(identifier), _mnemonic(identifier)
        fresh = True
        if code in self.codes:
            self.errors.append("%s repeats the id %s (%s)" % (label, code, self.codes[code]))
            fresh = False
        if mnemonic in self.mnemonics:
            self.errors.append("%s repeats the mnemonic %r (%s)" % (label, mnemonic, self.mnemonics[mnemonic]))
            fresh = False
        self.codes.setdefault(code, identifier)
        self.mnemonics.setdefault(mnemonic, identifier)
        return fresh


def _parse_parts(
    value: Any, catalogues: Catalogues, ids: _Ids, used: Set[str], errors: List[str]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """The printed and Bought Parts, each by id."""

    printed: Dict[str, Dict[str, Any]] = {}
    bought: Dict[str, Dict[str, Any]] = {}
    if not isinstance(value, list) or not value:
        errors.append("assembly_tree.parts must be a non-empty list")
        return printed, bought
    letters: Dict[str, Tuple[str, str]] = {}
    for index, item in enumerate(value):
        label = "assembly_tree.parts[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        match = PART_ID.fullmatch(identifier) if isinstance(identifier, str) else None
        if match is None:
            errors.append(
                "%s.id must be a code and a kebab-case mnemonic: A01-<name> to K99-<name> for a "
                "printed Part, P01-<name> for a Bought Part" % label
            )
            continue
        if not ids.add(identifier, label):
            continue
        if match.group(1) == "P":
            if set(item) != {"id", "bought"}:
                errors.append("%s: a Bought Part is exactly {id, bought}" % label)
                continue
            entry = catalogues.parts.get(item["bought"]) if isinstance(item["bought"], str) else None
            if entry is None:
                errors.append(
                    "%s.bought %r is not in the Bought Part catalogue; one outside it needs the "
                    "owner's approval, by adding it to bought-parts.json" % (label, item["bought"])
                )
                continue
            if entry.material:
                errors.append(
                    "%s.bought %r is a %s: tools and consumables go in assembly_tree.materials, "
                    "never in the tree" % (label, item["bought"], entry.category)
                )
                continue
            if not entry.confirmed:
                used.add("bought-parts.json:%s" % entry.id)
            bought[identifier] = item
            continue
        if set(item) != {"id", "name", "filament"}:
            errors.append("%s: a printed Part is exactly {id, name, filament}" % label)
            continue
        if not _text(item["name"], MAX_NAME_CHARS):
            errors.append("%s.name must name the Part in at most %d characters" % (label, MAX_NAME_CHARS))
            continue
        filament = catalogues.filaments.get(item["filament"]) if isinstance(item["filament"], str) else None
        if filament is None:
            errors.append(
                "%s.filament %r is not in the filament catalogue; a colour outside it needs the "
                "owner's approval, by adding it to filaments.json" % (label, item["filament"])
            )
            continue
        if not filament.confirmed:
            used.add("filaments.json:%s" % filament.id)
        letter = match.group(1)
        if letter in letters and letters[letter][0] != filament.id:
            errors.append(
                "%s: letter %s is %s (%s), so %s cannot be %s; one letter is one filament"
                % (label, letter, letters[letter][0], letters[letter][1], identifier, filament.id)
            )
            continue
        letters.setdefault(letter, (filament.id, identifier))
        printed[identifier] = item
    return printed, bought


def _parse_input(
    item: Any, label: str, needs_direction: Optional[bool], errors: List[str]
) -> Optional[Tuple[str, int]]:
    """One step input: ``(id, count)``. ``needs_direction`` is True for an
    input that moves in, False where a direction is refused, None where it
    is not checked here."""

    if not isinstance(item, dict) or not set(item) <= {"id", "direction", "count"}:
        errors.append("%s must be {id, direction, count} (direction and count optional)" % label)
        return None
    identifier = item.get("id")
    if not isinstance(identifier, str):
        errors.append("%s.id must name a Part, Print Piece or earlier step" % label)
        return None
    count = item.get("count", 1)
    if not _integer(count, 1, MAX_COUNT):
        errors.append("%s.count must be a whole number from 1 to %d" % (label, MAX_COUNT))
        return None
    if needs_direction is True and not _vector(item.get("direction")):
        errors.append(
            "%s.direction must be its one straight insertion direction, three numbers in the "
            "assembly frame, not all zero" % label
        )
        return None
    if needs_direction is False and "direction" in item:
        errors.append("%s takes no direction: it does not move into anything" % label)
        return None
    return identifier, count


def _parse_steps(
    value: Any, leaves: Mapping[str, str], ids: _Ids, errors: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[str, int]]]:
    """The steps in Manual order, and every input's parent: child id ->
    (step id, count per making of that step)."""

    steps: List[Dict[str, Any]] = []
    parent: Dict[str, Tuple[str, int]] = {}
    if not isinstance(value, list) or not value or len(value) > MAX_STEPS:
        errors.append("assembly_tree.steps must list 1 to %d Assembly Steps in Manual order" % MAX_STEPS)
        return steps, parent
    allowed = {"id", "output", "count", "joint", "inputs", "text", "error_prone", "leads",
               "lamps", "glue_reason"}
    known_steps: Set[str] = set()
    last_number = 0
    for index, item in enumerate(value):
        label = "assembly_tree.steps[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        match = STEP_ID.fullmatch(identifier) if isinstance(identifier, str) else None
        if match is None:
            errors.append("%s.id must look like S01-<kebab-case mnemonic>" % label)
            continue
        if not ids.add(identifier, label):
            continue
        number = int(match.group(1))
        if number <= last_number:
            errors.append("%s: step numbers rise in Manual order; %s follows S%02d" % (label, identifier, last_number))
        last_number = max(last_number, number)
        unknown = sorted(set(item) - allowed)
        if unknown:
            errors.append("%s has unknown field(s): %s" % (label, ", ".join(unknown)))
        valid = True
        if not _text(item.get("output"), MAX_OUTPUT_CHARS):
            errors.append("%s.output must name its Sub-assembly in at most %d characters" % (label, MAX_OUTPUT_CHARS))
            valid = False
        if not _integer(item.get("count"), 1, MAX_COUNT):
            errors.append("%s.count must be how many times it is made per toy, 1 to %d" % (label, MAX_COUNT))
            valid = False
        if not _text(item.get("text"), MAX_TEXT_CHARS):
            errors.append("%s.text must be one short English instruction of at most %d characters" % (label, MAX_TEXT_CHARS))
            valid = False
        if "error_prone" in item and not isinstance(item["error_prone"], bool):
            errors.append("%s.error_prone must be true or false" % label)
            valid = False
        joint = item.get("joint")
        if joint not in JOINTS:
            errors.append("%s.joint must be one of %s" % (label, ", ".join(JOINTS)))
            joint = None
            valid = False
        if joint == "glue":
            if not _text(item.get("glue_reason"), MAX_REASON_CHARS):
                errors.append("%s: glue is a last resort and needs its glue_reason" % label)
                valid = False
        elif "glue_reason" in item:
            errors.append("%s.glue_reason belongs to a glue joint only" % label)
            valid = False
        if joint == LEADS:
            lamps = item.get("lamps")
            if not isinstance(lamps, list) or not lamps or len(set(map(str, lamps))) != len(lamps):
                errors.append("%s: a leads step names the lamps whose leads it joins, each once" % label)
                valid = False
        elif "lamps" in item:
            errors.append("%s.lamps belongs to a leads step only" % label)
            valid = False
        inputs = item.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append("%s.inputs must be a non-empty list" % label)
            continue
        if joint in SHAPINGS and len(inputs) != 1:
            errors.append("%s: a %s step has exactly one input" % (label, joint))
            valid = False
        if joint in JOINS + (PAPER,) and len(inputs) < 2:
            errors.append("%s: a %s step joins two or more inputs" % (label, joint))
            valid = False
        parsed: List[Tuple[str, int]] = []
        for position, raw in enumerate(inputs):
            where = "%s.inputs[%d]" % (label, position)
            if joint in JOINS + (PAPER,):
                # The first input is what the others go into; it stays put.
                needs = position > 0
            elif joint is None:
                needs = None
            else:
                needs = False
            entry = _parse_input(raw, where, needs, errors)
            if entry is None:
                valid = False
                continue
            child, count = entry
            if child not in leaves and child not in known_steps:
                errors.append("%s.id %r is no Part, Print Piece or earlier step" % (where, child))
                valid = False
            elif child in parent:
                errors.append("%s.id %r is already an input of %s" % (where, child, parent[child][0]))
                valid = False
            else:
                parsed.append(entry)
        for child, count in parsed:
            parent[child] = (identifier, count)
        known_steps.add(identifier)
        if valid:
            steps.append(item)
    return steps, parent


def _leaves_under(node: str, children: Mapping[str, List[str]]) -> Set[str]:
    found: Set[str] = set()
    stack = [node]
    while stack:
        current = stack.pop()
        below = children.get(current)
        if below is None:
            found.add(current)
        else:
            stack.extend(below)
    return found


def _ancestors(node: str, parent: Mapping[str, Tuple[str, int]]) -> List[str]:
    chain = [node]
    while chain[-1] in parent:
        chain.append(parent[chain[-1]][0])
    return chain


def parse_assembly_tree(
    value: Any,
    geometries: Mapping[str, int],
    pieces: Sequence[Mapping[str, Any]],
    catalogues: Catalogues,
    errors: List[str],
) -> Optional[ContractAssemblyTree]:
    """Schema 7's ``assembly_tree``, or None after appending every failure.

    ``geometries`` maps each Unique Geometry id to its count; ``pieces`` are
    the ``print`` section's Print Pieces (already checked by its parser),
    which are leaves of the tree.
    """

    if not isinstance(value, dict):
        errors.append("assembly_tree must be an object with parts, steps and components (schema_version 7)")
        return None
    before = len(errors)
    unknown = sorted(set(value) - {"parts", "steps", "components", "materials"})
    if unknown:
        errors.append("assembly_tree has unknown field(s): %s" % ", ".join(unknown))
    ids = _Ids(errors)
    unconfirmed: Set[str] = set()
    printed, bought = _parse_parts(value.get("parts"), catalogues, ids, unconfirmed, errors)
    leaves: Dict[str, str] = {key: "printed" for key in printed}
    leaves.update({key: "bought" for key in bought})
    piece_by_id: Dict[str, Mapping[str, Any]] = {}
    for index, piece in enumerate(pieces):
        identifier = piece.get("id")
        if isinstance(identifier, str) and PIECE_ID.fullmatch(identifier):
            if ids.add(identifier, "print.pieces[%d]" % index):
                piece_by_id[identifier] = piece
                leaves[identifier] = "piece"
    steps, parent = _parse_steps(value.get("steps"), leaves, ids, errors)
    if len(errors) != before:
        # The tree is not whole: what follows would only echo these failures.
        _check_materials(value.get("materials"), catalogues, unconfirmed, errors)
        return None
    by_id = {step["id"]: step for step in steps}
    children: Dict[str, List[str]] = {step["id"]: [] for step in steps}
    for child, (step, _count) in parent.items():
        children[step].append(child)

    root = steps[-1]["id"]
    for leaf in leaves:
        if leaf not in parent:
            errors.append("%s is in no Assembly Step: every Part is a leaf of the tree" % leaf)
    for step in steps[:-1]:
        if step["id"] not in parent:
            errors.append(
                "%s's Sub-assembly is used by no later step; only the last step, %s, is the "
                "finished toy" % (step["id"], root)
            )
    if by_id[root]["count"] != 1:
        errors.append("%s is the finished toy, so it is made once" % root)

    # How many of each node one toy holds: a step's own count, a leaf's
    # from its parent step and the input count.
    totals: Dict[str, int] = {}
    for step in reversed(steps):
        identifier = step["id"]
        totals[identifier] = step["count"]
        if identifier in parent:
            above, per = parent[identifier]
            expected = by_id[above]["count"] * per
            if step["count"] != expected:
                errors.append(
                    "%s.count is %d, but %s takes %d of it and is made %d times: %d"
                    % (identifier, step["count"], above, per, by_id[above]["count"], expected)
                )
    for leaf in leaves:
        if leaf in parent:
            above, per = parent[leaf]
            totals[leaf] = by_id[above]["count"] * per

    _check_leads(steps, children, bought, catalogues, errors)
    _check_pieces(piece_by_id, leaves, by_id, parent, children, totals, errors)
    component_of = _check_components(
        value.get("components"), geometries, printed, bought, parent, children, totals, errors
    )
    _check_materials(value.get("materials"), catalogues, unconfirmed, errors)
    if len(errors) != before:
        return None
    return ContractAssemblyTree(
        section=value, component_of=component_of, unconfirmed=tuple(sorted(unconfirmed))
    )


def _check_leads(
    steps: Sequence[Mapping[str, Any]], children: Mapping[str, List[str]],
    bought: Mapping[str, Mapping[str, Any]], catalogues: Catalogues, errors: List[str],
) -> None:
    """A leads step sits at or above the smallest Sub-assembly holding every
    lamp it joins; a step that encloses a lead says where it comes out."""

    def lamp(identifier: Any) -> bool:
        entry = bought.get(identifier) if isinstance(identifier, str) else None
        return entry is not None and catalogues.parts[entry["bought"]].category == "lamp"

    for step in steps:
        below = _leaves_under(step["id"], children)
        for name in step.get("lamps") or ():
            if not lamp(name):
                errors.append("%s.lamps names %r, which is no lamp Bought Part" % (step["id"], name))
            elif name not in below:
                errors.append(
                    "%s joins the leads of %s, which is not yet in its Sub-assembly; a leads step "
                    "sits at or above the smallest Sub-assembly holding every lamp it joins"
                    % (step["id"], name)
                )
        leads = step.get("leads")
        if leads is None:
            continue
        if not isinstance(leads, list) or not leads:
            errors.append("%s.leads must list every lead the step encloses" % step["id"])
            continue
        for index, lead in enumerate(leads):
            label = "%s.leads[%d]" % (step["id"], index)
            if not isinstance(lead, dict) or set(lead) != {"lamp", "route_mm", "exit"}:
                errors.append("%s must be exactly {lamp, route_mm, exit}" % label)
                continue
            if not lamp(lead["lamp"]):
                errors.append("%s.lamp must name a lamp Bought Part" % label)
            elif lead["lamp"] not in below:
                errors.append("%s.lamp %s is not in this step's Sub-assembly" % (label, lead["lamp"]))
            route = lead["route_mm"]
            if (
                not isinstance(route, list) or len(route) < 2
                or any(
                    not isinstance(point, list) or len(point) != 3
                    or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in point)
                    for point in route
                )
            ):
                errors.append("%s.route_mm must be two or more [x, y, z] points in the assembly frame" % label)
            if not _text(lead["exit"], MAX_EXIT_CHARS):
                errors.append("%s.exit must say in at most %d characters where the lead comes out" % (label, MAX_EXIT_CHARS))


def _check_pieces(
    pieces: Mapping[str, Mapping[str, Any]], leaves: Mapping[str, str],
    steps: Mapping[str, Mapping[str, Any]], parent: Mapping[str, Tuple[str, int]],
    children: Mapping[str, List[str]], totals: Mapping[str, int], errors: List[str],
) -> None:
    """Each Print Piece lands on a printed Part, Bought Part or Sub-assembly
    that exists, is applied in a paper step once its host is there, and is
    printed as many times as the tree uses it."""

    for identifier, piece in sorted(pieces.items()):
        host = piece.get("on")
        if not isinstance(host, str) or (leaves.get(host) not in ("printed", "bought") and host not in steps):
            errors.append(
                "%s.on %r names nothing that exists: name a printed Part, a Bought Part or a "
                "step's Sub-assembly" % (identifier, host)
            )
            continue
        copies = piece.get("count", 1)
        if identifier in totals and copies != totals[identifier]:
            errors.append(
                "%s prints %d cop%s, but the tree applies it %d time%s"
                % (identifier, copies, "y" if copies == 1 else "ies", totals[identifier],
                   "" if totals[identifier] == 1 else "s")
            )
        # The step that applies it: the first step above it that joins.
        applying = None
        for node in _ancestors(identifier, parent)[1:]:
            if len(children[node]) > 1:
                applying = node
                break
        if applying is None:
            errors.append("%s is never applied: no step above it joins it to its host" % identifier)
            continue
        if steps[applying].get("joint") != PAPER:
            errors.append("%s is applied in %s, whose joint is %s, not paper"
                          % (identifier, applying, steps[applying].get("joint")))
        inside = host in _leaves_under(applying, children) or _below(host, applying, parent)
        if host == applying or not inside:
            errors.append(
                "%s is applied in %s, before its host %s is part of that Sub-assembly"
                % (identifier, applying, host)
            )


def _below(node: str, step: str, parent: Mapping[str, Tuple[str, int]]) -> bool:
    return step in _ancestors(node, parent)[1:]


def _check_components(
    value: Any, geometries: Mapping[str, int], printed: Mapping[str, Any],
    bought: Mapping[str, Any], parent: Mapping[str, Tuple[str, int]],
    children: Mapping[str, List[str]], totals: Mapping[str, int], errors: List[str],
) -> Dict[str, str]:
    """Each Component is one contiguous subtree, one per Unique Geometry, and
    every printed and Bought Part belongs to exactly one."""

    owner: Dict[str, str] = {}
    if not isinstance(value, list) or not value:
        errors.append("assembly_tree.components must list one Component per Unique Geometry")
        return owner
    solid = set(printed) | set(bought)
    named: Set[str] = set()
    for index, item in enumerate(value):
        label = "assembly_tree.components[%d]" % index
        if not isinstance(item, dict) or set(item) != {"geometry", "parts"}:
            errors.append("%s must be exactly {geometry, parts}" % label)
            continue
        geometry = item["geometry"]
        if geometry not in geometries:
            errors.append("%s.geometry %r is no Unique Geometry" % (label, geometry))
            continue
        if geometry in named:
            errors.append("%s.geometry %r already has its Component" % (label, geometry))
            continue
        named.add(geometry)
        parts = item["parts"]
        if not isinstance(parts, list) or not parts or len(set(map(str, parts))) != len(parts):
            errors.append("%s.parts must list its printed and Bought Parts, each once" % label)
            continue
        valid = True
        for part in parts:
            if part not in solid:
                errors.append("%s.parts names %r, which is no printed or Bought Part" % (label, part))
                valid = False
            elif part in owner:
                errors.append("%s is in two Components: %s and %s" % (part, owner[part], geometry))
                valid = False
        if not valid:
            continue
        for part in parts:
            owner[part] = geometry
        # The Component's root is the lowest step holding all its Parts.
        chains = [_ancestors(part, parent) for part in parts]
        common = [node for node in chains[0] if all(node in chain for chain in chains[1:])]
        if not common:
            errors.append("%s's Parts are not in one tree" % geometry)
            continue
        top = common[0]
        extra = sorted((_leaves_under(top, children) & solid) - set(parts))
        if extra:
            errors.append(
                "Component %s is not one contiguous subtree: its smallest Sub-assembly, %s, also "
                "holds %s" % (geometry, top, ", ".join(extra))
            )
            continue
        if totals.get(top) != geometries[geometry]:
            errors.append(
                "Component %s's subtree, %s, is made %s time(s) per toy, but the geometry's count "
                "is %d" % (geometry, top, totals.get(top), geometries[geometry])
            )
    for geometry in sorted(set(geometries) - named):
        errors.append("Unique Geometry %s has no Component in assembly_tree.components" % geometry)
    listed = {
        part for item in value if isinstance(item, dict) and isinstance(item.get("parts"), list)
        for part in item["parts"] if isinstance(part, str)
    }
    for part in sorted(solid - listed):
        errors.append("%s belongs to no Component" % part)
    return owner


def _check_materials(value: Any, catalogues: Catalogues, unconfirmed: Set[str], errors: List[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list) or len(set(map(str, value))) != len(value):
        errors.append("assembly_tree.materials must list catalogue tools and consumables, each once")
        return
    for name in value:
        entry = catalogues.parts.get(name) if isinstance(name, str) else None
        if entry is None:
            errors.append(
                "assembly_tree.materials names %r, which is not in the Bought Part catalogue; one "
                "outside it needs the owner's approval" % (name,)
            )
        elif not entry.material:
            errors.append(
                "assembly_tree.materials names %r, a %s: a Bought Part the buyer assembles is a "
                "Part of the tree" % (name, entry.category)
            )
        elif not entry.confirmed:
            unconfirmed.add("bought-parts.json:%s" % entry.id)


__all__ = [
    "ContractAssemblyTree",
    "JOINS",
    "JOINTS",
    "LEADS",
    "PAPER",
    "PART_ID",
    "PIECE_ID",
    "SHAPINGS",
    "STEP_ID",
    "parse_assembly_tree",
]
