#!/usr/bin/env python3
"""The Assembly Tree gates of a schema 7 Design Contract (ADR 0092 decision 8).

    kit_tree.py --install <cad-project> --wish <run>/WISH.json
    kit_tree.py <cad-project> --component <geometry> [--nozzle 0.4] [--json]
    kit_tree.py <cad-project> --assembly [--nozzle 0.4] [--json]
    kit_tree.py <cad-project> --final [--nozzle 0.4] [--json]
    kit_tree.py --self-check

A schema 7 contract splits the toy into kit Parts: printed bodies, each in one
catalogued filament; Bought Parts from the owner's catalogue; and Print
Pieces, the paper the ``print`` section lays out. Its Assembly Tree joins them
in Manual order, and each Component is a chosen subtree. These gates compare
that tree with what Make built. They are deterministic; none of them judges.

How a Part is a STEP body
-------------------------
A Component's ``part_<geometry>.step.py`` ``gen_step()`` returns one labelled
solid per printed Part of the Component: the label is the Part id
(``A01-desk``). A Component that holds Bought Parts also defines
``bought_parts()``, which returns one labelled body per Bought Part
(``P01-steel-pin``), modelled to its catalogue size, in the same frame as
``gen_step()``; it is never printed, so the print gates never see it. When one
Component instance holds a Part more than once (four legs), the copies are
labelled ``<id>#1`` to ``<id>#4``. Every body is placed into the assembly by
the Component's own ``assembly_pose(shape, None)`` (``instance=n`` for the
n-th instance of a geometry whose count is above 1), which moves the shape as
a whole and keeps its labels. A labelled node is one body; an unlabelled node
is looked through; a solid reached without a Part label is an extra body.

The gates
---------
- **Reconciliation.** Every body, every Print Piece and every cited Bought
  Part matches exactly one leaf. A missing, extra or duplicated Part (a label
  twice, one label on two solids, a body no leaf names, a Part of another
  Component) is a **tree defect**. So is a Print Piece or Bought Part the
  sealed install cannot account for, and a leads step below the smallest
  Sub-assembly holding its lamps. In the pilot (ADR 0092 decision 10) a
  tree defect stops the run: nothing repairs the tree automatically.
- **Colour.** Every printed Part's body carries its filament's colour, so
  the review renders show the kit as it prints.
- **Insertion.** Each Assembly Step that joins (a joint of peg-socket,
  tab-slot, pin-hinge, foam-tape, glue or paper) becomes one
  ``assembly_sequence`` of ``linear_motion_collision`` conditions
  (``check_motion``, ADR 0088), in Manual order. Its first input is the base
  and stays put. Every later input, each copy of it on its own, is swept from
  its seat back along its declared direction until it is wholly outside the
  bounds of the rest of the step's Sub-assembly, against only what is
  already assembled: the base and the inputs before it. Overlap above
  0.001 mm3 fails; seated contact at the seat is allowed. The sweep samples
  no coarser than the thinnest wall it could miss: the smaller of two print
  lines and the involved geometries' ``wall_min_mm``. An input blocked only by
  an input of the same step that went in before it can go in only together
  with it: a simultaneous move, refused. Every joint the input engages at
  its seat must slide along the direction: each pair of mating faces (two
  parallel flat faces, or two cylinders or cones on parallel axes, within
  ``JOINT_GAP_MM``) faces along or across it, or has its axis along it. A
  pair at an angle is a non-parallel joint.
- **Lead routes.** A sphere of the lead's diameter (the lamp's catalogue
  ``lead diameter``) plus ``LEAD_CLEARANCE_MM`` is swept along each declared
  route; any printed body of the step's Sub-assembly in its way closes it.

Where each check runs: a step all of whose Parts belong to one Component is
checked in that Component's round (``--component``); a step across
Components in assembly rounds (``--assembly``) and in final verification
(``--final``, which also reconciles every Component and writes
``measure/tree-report.json`` for the host). The ``paper`` gate follows the same
split: :func:`paper_plan` says which Component round checks each Print Piece.

Exit status: 0 pass, 1 a repairable failure, 3 a tree defect, 2 bad usage.
The last stdout line is the JSON report with ``--json``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

KIT_DIR = "tree"
KIT_FILE = "kit.json"
REPORT_FILE = "tree-report.json"
KIT_KIND = "kit-tree"
REPORT_KIND = "kit-tree-report"
INSTALL_SCHEMA = 1
TREE_SCHEMA_VERSION = 7
# The pilot's ledger of tree defects (ADR 0092 decision 10), under measure/.
DEFECTS_FILE = "tree-defects.json"

JOINS = ("peg-socket", "tab-slot", "pin-hinge", "foam-tape", "glue")
PAPER = "paper"
LEADS = "leads"
SWEPT = JOINS + (PAPER,)

OVERLAP_MM3 = 0.001          # contact is not collision (check_motion's default)
OUTSIDE_MARGIN_MM = 1.0      # how far past the Sub-assembly's bounds a sweep starts
LEAD_CLEARANCE_MM = 0.4      # 0.2 mm all round the lead: a cadfits slip fit
JOINT_GAP_MM = 0.3           # a face this close to what it joins is a joint face
PARALLEL_TOLERANCE_DEG = 2.0
PRINT_LINES = 2              # the thinnest printable wall, in lines

DEFECT = "defect"
FAILURE = "failure"
PART_LABEL = re.compile(r"^([A-KP][0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*)(?:#([1-9][0-9]*))?$")
EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_DEFECT = 0, 1, 2, 3


# ---------------------------------------------------------------------------
# install


def install_document(contract: dict, catalogue: dict | None) -> dict:
    """The exact install a sealed schema 7 contract and its catalogue
    snapshot give. The host builds the same document to check Make."""

    if not isinstance(contract, dict) or contract.get("schema_version") != TREE_SCHEMA_VERSION:
        raise ValueError("the sealed Design Contract is not schema 7: it has no Assembly Tree")
    if not isinstance(catalogue, dict):
        raise ValueError("the Wish seals no kit_catalogue beside its schema 7 contract")
    section = contract.get("print")
    return {
        "kind": KIT_KIND,
        "schema_version": INSTALL_SCHEMA,
        "assembly_tree": contract.get("assembly_tree"),
        "geometries": contract.get("geometries"),
        "pieces": (section.get("pieces") if isinstance(section, dict) else None) or [],
        "catalogue": catalogue,
    }


def wish_document(wish: dict) -> dict:
    context = wish.get("context") if isinstance(wish, dict) else None
    if not isinstance(context, dict):
        raise ValueError("the Wish has no context")
    return install_document(context.get("design_contract"), context.get("kit_catalogue"))


def document_bytes(document: dict) -> bytes:
    return (json.dumps(document, indent=1, sort_keys=True) + "\n").encode("utf-8")


def tree_digest(document: dict) -> str:
    return hashlib.sha256(document_bytes(document)).hexdigest()


def install(project: Path, wish_path: Path) -> dict:
    """Write ``tree/kit.json`` from the sealed Wish. Refuses an existing
    install with other bytes: it is never edited."""

    project = Path(project)
    if not project.is_dir():
        raise ValueError("%s: not a CAD project directory" % project)
    document = wish_document(json.loads(Path(wish_path).read_text(encoding="utf-8")))
    data = document_bytes(document)
    target = project / KIT_DIR / KIT_FILE
    if target.exists() and target.read_bytes() != data:
        raise ValueError("%s exists with other bytes; the tree install is never edited" % target)
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)
    return {"installed": str(target), "sha256": hashlib.sha256(data).hexdigest()}


def read_install(project: Path) -> dict | None:
    try:
        document = json.loads((Path(project) / KIT_DIR / KIT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None


def install_state(project: Path, expected: dict | None) -> tuple[dict | None, str | None]:
    """``(install, error)``. ``expected`` is the document the sealed Wish
    gives, or None outside a run, where the installed one stands (the host
    checks it against the seal)."""

    installed = read_install(project)
    if installed is None:
        return expected, ("the Assembly Tree is not installed: run kit_tree.py --install <cad-project> "
                          "--wish <run>/WISH.json")
    if expected is not None and installed != expected:
        return expected, ("tree/kit.json is not the sealed contract's Assembly Tree: reinstall it "
                          "from WISH.json; it is never edited")
    if installed.get("kind") != KIT_KIND or installed.get("schema_version") != INSTALL_SCHEMA:
        return None, "tree/kit.json is not a kit tree install"
    return installed, None


# ---------------------------------------------------------------------------
# the tree, read from the install


class Plan:
    """The installed tree: who is under whom, how many, and which Component
    owns each Part. Every lookup is deterministic and reads no geometry."""

    def __init__(self, kit: dict) -> None:
        tree = kit["assembly_tree"]
        self.kit = kit
        self.parts = {item["id"]: item for item in tree["parts"]}
        self.printed = [key for key, item in self.parts.items() if "filament" in item]
        self.bought = [key for key, item in self.parts.items() if "bought" in item]
        self.pieces = {item["id"]: item for item in kit.get("pieces") or ()}
        self.steps = list(tree["steps"])
        self.step = {item["id"]: item for item in self.steps}
        self.children: dict[str, list[str]] = {}
        self.inputs: dict[str, list[dict]] = {}
        self.parent: dict[str, tuple[str, int]] = {}
        for item in self.steps:
            self.inputs[item["id"]] = list(item["inputs"])
            self.children[item["id"]] = [entry["id"] for entry in item["inputs"]]
            for entry in item["inputs"]:
                self.parent[entry["id"]] = (item["id"], int(entry.get("count", 1)))
        self.root = self.steps[-1]["id"]
        self.geometries = {item["id"]: item for item in kit["geometries"]}
        self.component_of: dict[str, str] = {}
        self.component_parts: dict[str, list[str]] = {}
        for item in tree["components"]:
            self.component_parts[item["geometry"]] = list(item["parts"])
            for part in item["parts"]:
                self.component_of[part] = item["geometry"]
        self.catalogue = kit.get("catalogue") or {}
        self.totals = self._totals()

    # -- counts and owners ---------------------------------------------------

    def _totals(self) -> dict[str, int]:
        totals = {self.root: int(self.step[self.root]["count"])}
        for item in reversed(self.steps):
            node = item["id"]
            totals.setdefault(node, int(item["count"]))
            for entry in item["inputs"]:
                totals[entry["id"]] = totals[node] * int(entry.get("count", 1))
        return totals

    def leaves_under(self, node: str) -> list[str]:
        if node not in self.children:
            return [node]
        found = []
        for child in self.children[node]:
            found += [leaf for leaf in self.leaves_under(child) if leaf not in found]
        return found

    def solid(self, leaf: str) -> bool:
        return leaf in self.parts

    def owners(self, node: str) -> set[str]:
        return {self.component_of[leaf] for leaf in self.leaves_under(node) if leaf in self.component_of}

    def scope(self, node: str) -> str | None:
        """The one Component a node lies wholly inside, or None when it spans
        Components (or holds no Part at all)."""

        owners = self.owners(node)
        return next(iter(owners)) if len(owners) == 1 else None

    def spans(self, node: str) -> bool:
        return len(self.owners(node)) > 1

    def ancestors(self, node: str) -> list[str]:
        chain = [node]
        while chain[-1] in self.parent:
            chain.append(self.parent[chain[-1]][0])
        return chain

    def instance_root(self, geometry: str) -> str:
        """The highest node wholly inside the Component: its subtree, plus
        any step above it that adds only paper."""

        parts = self.component_parts[geometry]
        chains = [self.ancestors(part) for part in parts]
        node = next(item for item in chains[0] if all(item in chain for chain in chains[1:]))
        count = self.geometries[geometry]["count"]
        while node in self.parent:
            above = self.parent[node][0]
            if self.owners(above) != {geometry} or self.totals[above] != count:
                break
            node = above
        return node

    def per_instance(self, geometry: str, node: str) -> int:
        return self.totals[node] // self.geometries[geometry]["count"]

    # -- occurrences ---------------------------------------------------------

    def occurrences(self, node: str, k: int) -> list[tuple[str, int]]:
        """The leaf occurrences under occurrence ``k`` of ``node``, numbered
        within the same scope: copy ``k`` of a step takes the next ``count``
        occurrences of each input, in Manual order."""

        if node not in self.children:
            return [(node, k)]
        found = []
        for entry in self.inputs[node]:
            per = int(entry.get("count", 1))
            for j in range((k - 1) * per + 1, k * per + 1):
                found += self.occurrences(entry["id"], j)
        return found

    def scope_counts(self, top: str) -> dict[str, int]:
        """How many occurrences of every node lie under one occurrence of ``top``."""

        counts = {top: 1}
        stack = [top]
        while stack:
            node = stack.pop()
            for entry in self.inputs.get(node, ()):
                counts[entry["id"]] = counts.get(entry["id"], 0) + counts[node] * int(entry.get("count", 1))
                stack.append(entry["id"])
        return counts

    def expected_labels(self, geometry: str) -> Counter:
        """Every body label one instance of a Component must hold."""

        counts = self.scope_counts(self.instance_root(geometry))
        labels: Counter = Counter()
        for part in self.component_parts[geometry]:
            many = counts.get(part, 0)
            if many == 1:
                labels[part] += 1
            for j in range(1, many + 1 if many > 1 else 1):
                labels["%s#%d" % (part, j)] += 1
        return labels

    # -- steps and paper -----------------------------------------------------

    def steps_in(self, scope: str | None) -> list[dict]:
        """The steps checked in one Component's round (``scope`` its id) or
        across Components (None), in Manual order."""

        chosen = []
        for item in self.steps:
            owners = self.owners(item["id"])
            if not owners:
                continue
            if (scope is None and len(owners) > 1) or (scope is not None and owners == {scope}):
                chosen.append(item)
        return chosen

    def lead_diameter(self, lamp: str) -> float | None:
        entry = (self.catalogue.get("bought_parts") or {}).get(self.parts[lamp].get("bought"), {})
        for size in entry.get("sizes") or ():
            if isinstance(size, dict) and size.get("what") == "lead diameter":
                values = size.get("mm") or size.get("max_mm") or ()
                if values:
                    return float(values[0])
        return None

    def wall_mm(self, geometries, nozzle: float) -> float:
        walls = [float(self.geometries[g]["wall_min_mm"]) for g in geometries if g in self.geometries]
        return min([PRINT_LINES * nozzle, *walls])


def structure_defects(plan: Plan) -> list[dict]:
    """The two sides of the three-way reconciliation that read no geometry:
    every Print Piece and every cited Bought Part matches exactly one leaf,
    and every leads step sits at or above its lamps' smallest common
    Sub-assembly."""

    defects = []
    leaves = Counter(entry["id"] for item in plan.steps for entry in item["inputs"]
                     if entry["id"] not in plan.step)
    piece_leaves = {leaf for leaf in leaves if re.match(r"^[MN][0-9]{2}-", leaf)}
    for piece in sorted(set(plan.pieces) - piece_leaves):
        defects.append(_defect("extra", piece, "a Print Piece the print section lays out is in no Assembly Step"))
    for piece in sorted(piece_leaves - set(plan.pieces)):
        defects.append(_defect("missing", piece, "an Assembly Step applies a Print Piece the print section does not lay out"))
    for leaf, many in sorted(leaves.items()):
        if many > 1:
            defects.append(_defect("duplicated", leaf, "is an input of %d steps; a Part is one leaf" % many))
    catalogue = plan.catalogue.get("bought_parts") or {}
    for part in plan.bought:
        if part not in leaves:
            defects.append(_defect("extra", part, "a Bought Part the tree cites is in no Assembly Step"))
        if plan.parts[part]["bought"] not in catalogue:
            defects.append(_defect("missing", part, "cites %s, which the sealed catalogue does not hold"
                                   % plan.parts[part]["bought"]))
    for part in plan.printed:
        if part not in leaves:
            defects.append(_defect("extra", part, "a printed Part is in no Assembly Step"))
    for part in plan.parts:
        if part not in plan.component_of:
            defects.append(_defect("extra", part, "belongs to no Component"))
    for item in plan.steps:
        if item.get("joint") != LEADS:
            continue
        under = set(plan.leaves_under(item["id"]))
        for lamp in item.get("lamps") or ():
            if lamp not in under:
                defects.append(_defect(
                    "misplaced", item["id"],
                    "joins the leads of %s below the smallest Sub-assembly holding every lamp it joins" % lamp))
    return defects


def _defect(kind: str, part: str, detail: str, **extra) -> dict:
    return {"kind": kind, "part": part, "detail": detail, **extra}


def paper_plan(kit: dict) -> dict:
    """Where the paper gate checks each Print Piece (ADR 0092 decision 8):
    ``{"hosted": {geometry: [piece]}, "bought": {geometry: [piece]},
    "spanning": {piece: [geometry]}}``. A piece on a printed Part, or on a
    Sub-assembly inside one Component, is that Component's round's to check.
    A piece on a Bought Part has no printed feature: its Component reports
    it. A piece on a Sub-assembly across Components may be carried by any of
    them; assembly rounds and final verification need exactly one."""

    plan = Plan(kit)
    hosted: dict[str, list[str]] = {}
    bought: dict[str, list[str]] = {}
    spanning: dict[str, list[str]] = {}
    for piece, item in sorted(plan.pieces.items()):
        host = item.get("on")
        if host in plan.bought:
            bought.setdefault(plan.component_of[host], []).append(piece)
        elif host in plan.printed:
            hosted.setdefault(plan.component_of[host], []).append(piece)
        elif host in plan.step:
            owners = sorted(plan.owners(host))
            if len(owners) == 1:
                hosted.setdefault(owners[0], []).append(piece)
            elif owners:
                spanning[piece] = owners
    return {"hosted": hosted, "bought": bought, "spanning": spanning}


def paper_roles(kit: dict) -> set[str]:
    """Every Component whose round runs the paper gate."""

    plan = paper_plan(kit)
    return set(plan["hosted"]) | set(plan["bought"]) | {g for owners in plan["spanning"].values() for g in owners}


def paper_coverage(kit: dict, passes: dict[str, set]) -> list[str]:
    """Each Print Piece on a Sub-assembly across Components passes in
    exactly one of their parts. ``passes`` maps a Component to the pieces its
    paper gate passed."""

    failures = []
    for piece, owners in sorted(paper_plan(kit)["spanning"].items()):
        carried = sorted(owner for owner in owners if piece in (passes.get(owner) or ()))
        if not carried:
            failures.append("%s: no part of %s carries its print feature" % (piece, ", ".join(owners)))
        elif len(carried) > 1:
            failures.append("%s: %s each carry its print feature; one piece has one place"
                            % (piece, " and ".join(carried)))
    return failures


# ---------------------------------------------------------------------------
# geometry: one interface, a build123d backend and test fakes


class Body:
    """One placed body: ``key`` is its leaf and occurrence in the scope
    (``A05-leg#3``), ``label`` the label it carried (None when it had none)."""

    def __init__(self, label, shape, *, solids: int = 1, colours=(), key: str | None = None) -> None:
        self.label = label
        self.shape = shape
        self.solids = solids
        self.colours = tuple(colours)
        self.key = key


def reconcile(expected: Counter, bodies: list[Body], plan: Plan, geometry: str) -> list[dict]:
    """Missing, extra and duplicated Parts of one Component instance."""

    defects = []
    found = Counter(body.label for body in bodies if body.label is not None)
    for label in sorted(expected):
        if found[label] == 0:
            defects.append(_defect("missing", label, "part_%s builds no body labelled %s" % (geometry, label),
                                   component=geometry))
        elif found[label] > 1:
            defects.append(_defect("duplicated", label, "part_%s builds %d bodies labelled %s"
                                   % (geometry, found[label], label), component=geometry))
    for label in sorted(set(found) - set(expected)):
        match = PART_LABEL.match(label)
        owner = plan.component_of.get(match.group(1)) if match else None
        why = ("is a Part of %s" % owner if owner not in (None, geometry)
               else "is no Part of the tree" if owner is None
               else "is one copy more than the tree holds")
        defects.append(_defect("extra", label, "part_%s builds a body labelled %s, which %s"
                               % (geometry, label, why), component=geometry))
    for body in bodies:
        if body.label is None:
            defects.append(_defect("extra", "(unlabelled)", "part_%s builds %d solid(s) with no Part label"
                                   % (geometry, body.solids), component=geometry))
        elif body.solids != 1 and body.label in expected and PART_LABEL.match(body.label).group(1) in plan.printed:
            # A bought STEP may import as several solids; a printed Part is one.
            defects.append(_defect("duplicated", body.label, "%s is %d solids; one printed Part is one solid"
                                   % (body.label, body.solids), component=geometry))
    return defects


def colour_failures(plan: Plan, bodies: list[Body]) -> list[str]:
    failures = []
    filaments = plan.catalogue.get("filaments") or {}
    for body in bodies:
        match = PART_LABEL.match(body.label or "")
        part = plan.parts.get(match.group(1)) if match else None
        if part is None or "filament" not in part:
            continue
        want = (filaments.get(part["filament"]) or {}).get("hex")
        if want is None:
            continue
        wrong = sorted({colour or "uncoloured" for colour in body.colours if not _same_colour(colour, want)})
        if not body.colours or wrong:
            failures.append("%s is %s, not its filament %s (%s): colour it %s"
                            % (body.label, ", ".join(wrong) or "uncoloured", part["filament"], want, want))
    return failures


def _same_colour(found: str | None, want: str) -> bool:
    if not found:
        return False
    a = [int(found[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(want[i:i + 2], 16) for i in (1, 3, 5)]
    return all(abs(x - y) <= 2 for x, y in zip(a, b))


def _unit(vector) -> tuple:
    length = math.sqrt(sum(float(v) ** 2 for v in vector))
    return tuple(float(v) / length for v in vector)


def _projection(bounds, direction) -> tuple[float, float]:
    lo, hi = bounds
    values = [sum(c * d for c, d in zip(corner, direction))
              for corner in ((x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2]))]
    return min(values), max(values)


def travel_mm(moving_bounds, other_bounds, direction) -> float:
    """How far back along ``direction`` the input starts: wholly outside the
    bounds of the rest of the Sub-assembly, plus a margin."""

    unit = _unit(direction)
    _low, moving_high = _projection(moving_bounds, unit)
    other_low, _high = _projection(other_bounds, unit)
    return max(OUTSIDE_MARGIN_MM, moving_high - other_low + OUTSIDE_MARGIN_MM)


def _check(scope: str | None, plan: Plan, geometry, bodies: dict[str, Body], nozzle: float) -> dict:
    """Every insertion and lead route of one scope against its bodies."""

    report = {"conditions": [], "failures": [], "routes": []}
    for item in plan.steps_in(scope):
        step = item["id"]
        involved = sorted(plan.owners(step))
        wall = plan.wall_mm(involved, nozzle)
        copies = _copies(plan, scope, step)
        if item.get("joint") in SWEPT:
            sequence = {"id": step, "check": "assembly_sequence", "description": item["text"],
                        "inputs": {"steps": []}}
            for k in copies:
                _insert_step(plan, geometry, bodies, item, k, wall, sequence, report)
            if sequence["inputs"]["steps"]:
                report["conditions"].append(sequence)
        for index, lead in enumerate(item.get("leads") or ()):
            _route(plan, geometry, bodies, item, copies, index, lead, report)
    return report


def _copies(plan: Plan, scope: str | None, step: str) -> list[int]:
    if scope is None:
        return list(range(1, plan.totals[step] + 1))
    return list(range(1, plan.per_instance(scope, step) + 1))


def _bodies_of(plan: Plan, bodies: dict[str, Body], node: str, k: int, solid_only=False) -> list[Body]:
    found = []
    for leaf, j in plan.occurrences(node, k):
        if solid_only and leaf not in plan.printed:
            continue
        body = bodies.get("%s#%d" % (leaf, j))
        if body is not None:
            found.append(body)
    return found


def _insert_step(plan, geometry, bodies, item, k, wall, sequence, report) -> None:
    step = item["id"]
    inputs = plan.inputs[step]
    base = inputs[0]
    per = int(base.get("count", 1))
    assembled = []
    for j in range((k - 1) * per + 1, k * per + 1):
        assembled += [(base["id"], body) for body in _bodies_of(plan, bodies, base["id"], j)]
    whole = _bodies_of(plan, bodies, step, k)
    for entry in inputs[1:]:
        per = int(entry.get("count", 1))
        direction = _unit(entry["direction"])
        for j in range((k - 1) * per + 1, k * per + 1):
            moving = _bodies_of(plan, bodies, entry["id"], j)
            if not moving:
                continue   # paper: the paper gate checks where it lands
            name = "%s#%d" % (entry["id"], j)
            others = [body for body in whole if body not in moving]
            if not assembled or not others:
                assembled += [(entry["id"], body) for body in moving]
                continue
            travel = travel_mm(geometry.bounds([b.shape for b in moving]),
                               geometry.bounds([b.shape for b in others]), direction)
            steps = max(1, math.ceil(travel / wall - 1e-9))
            condition = {
                "id": "%s.%s" % (step, name) if plan.totals[step] == 1 else "%s#%d.%s" % (step, k, name),
                "check": "linear_motion_collision",
                "expect": "clear",
                "description": "%s goes in alone along %s" % (name, list(entry["direction"])),
                "inputs": {"moving_part": name, "obstacle_parts": [body.key for _, body in assembled],
                           "translation": [round(-c * travel, 6) for c in direction],
                           "steps": steps, "allow_seated_contact": True},
                "thresholds": {"maxOverlapMm3": OVERLAP_MM3, "maxStepMm": round(wall, 6)},
            }
            sequence["inputs"]["steps"].append(condition)
            result = geometry.sweep(condition, moving, [body for _, body in assembled])
            condition["result"] = {key: result.get(key) for key in ("status", "detail", "obstacle", "overlapMm3")
                                   if key in result}
            if result.get("status") != "pass":
                obstacle = result.get("obstacle")
                sibling = next((source for source, body in assembled if body.key == obstacle), None)
                simultaneous = False
                if sibling is not None and sibling != base["id"] and result.get("status") == "fail":
                    # Blocked on the way, not at the seat, and clear without
                    # that sibling: the two go in only together.
                    blocker = [body for source, body in assembled if source == sibling]
                    seated = geometry.sweep(_at_seat(condition), moving, blocker)
                    rest = [body for source, body in assembled if source != sibling]
                    again = geometry.sweep({**condition, "id": condition["id"] + ".alone"}, moving, rest)
                    simultaneous = seated.get("status") == "pass" and again.get("status") == "pass"
                if simultaneous:
                    report["failures"].append(
                        "%s: %s is blocked only by %s, which went in before it in the same step: they go in "
                        "only together, a simultaneous move; each input is inserted alone (ADR 0092)"
                        % (step, name, obstacle))
                else:
                    report["failures"].append("%s: %s cannot go in alone along %s: %s"
                                              % (step, name, list(entry["direction"]), result.get("detail")))
            for face in geometry.nonparallel([b.shape for b in moving], [b.shape for _, b in assembled],
                                             direction):
                report["failures"].append("%s: %s engages a joint that is not parallel to its direction %s: %s"
                                          % (step, name, list(entry["direction"]), face))
            assembled += [(entry["id"], body) for body in moving]


def _at_seat(condition: dict) -> dict:
    """The same condition held at the seat: does the input overlap the
    obstacle where it sits?"""

    inputs = {**condition["inputs"], "translation": [0.0, 0.0, 0.0], "steps": 1, "allow_seated_contact": False}
    thresholds = {key: value for key, value in condition["thresholds"].items() if key != "maxStepMm"}
    return {**condition, "id": condition["id"] + ".seat", "inputs": inputs, "thresholds": thresholds}


def _route(plan, geometry, bodies, item, copies, index, lead, report) -> None:
    step = item["id"]
    diameter = plan.lead_diameter(lead["lamp"])
    label = "%s.leads[%d]" % (step, index)
    if diameter is None:
        report["failures"].append(
            "%s: the sealed catalogue gives %s no lead diameter, so its route cannot be swept"
            % (label, plan.parts[lead["lamp"]]["bought"]))
        return
    obstacles = []
    for k in copies:
        obstacles += _bodies_of(plan, bodies, step, k, solid_only=True)
    size = diameter + LEAD_CLEARANCE_MM
    result = geometry.route(lead["route_mm"], size, obstacles)
    record = {"id": label, "lamp": lead["lamp"], "sphere_mm": round(size, 6), "route_mm": lead["route_mm"],
              "clear": bool(result.get("clear")), "blocked_by": result.get("blocked_by") or []}
    report["routes"].append(record)
    if not record["clear"]:
        report["failures"].append(
            "%s: the lead of %s is closed: a %.2f mm sphere swept along its route meets %s"
            % (label, lead["lamp"], size,
               ", ".join("%s (%.4g mm3)" % (b["obstacle"], b["overlapMm3"]) for b in record["blocked_by"])
               or result.get("detail", "an unmeasured body")))


def keyed(plan: Plan, geometry: str, bodies: list[Body], instance: int = 1) -> dict[str, Body]:
    """Bodies of one Component instance by their scope key. ``instance``
    numbers the occurrences across the whole toy."""

    counts = plan.scope_counts(plan.instance_root(geometry))
    found = {}
    for body in bodies:
        match = PART_LABEL.match(body.label or "")
        if match is None or plan.component_of.get(match.group(1)) != geometry:
            continue
        part, local = match.group(1), int(match.group(2) or 1)
        many = counts.get(part, 0)
        body.key = "%s#%d" % (part, (instance - 1) * many + local)
        found[body.key] = body
    return found


def check_component(plan: Plan, geometry, role: str, nozzle: float) -> dict:
    """Everything one Component's round checks: its bodies against its
    leaves, their colours, and every step and route wholly inside it."""

    report = {"scope": "component:%s" % role, "defects": [], "failures": [], "conditions": [], "routes": []}
    expected = plan.expected_labels(role)
    instances = geometry.instances(role)
    for instance in instances:
        bodies = geometry.component(role, instance)
        defects = reconcile(expected, bodies, plan, role)
        for defect in defects:
            if len(instances) > 1:
                defect["instance"] = instance
        report["defects"] += defects
        report["failures"] += colour_failures(plan, bodies)
        if defects:
            continue
        checked = _check(role, plan, geometry, keyed(plan, role, bodies), nozzle)
        for key in ("conditions", "failures", "routes"):
            report[key] += checked[key]
    report["failures"] = list(dict.fromkeys(report["failures"]))
    return report


def check_assembly(plan: Plan, geometry, nozzle: float, *, reconcile_all: bool = False) -> dict:
    """The checks across Components: every placed instance, then every step
    and route that spans Components. ``reconcile_all`` (final verification)
    also reconciles and colour-checks every Component."""

    report = {"scope": "final" if reconcile_all else "assembly", "defects": structure_defects(plan),
              "failures": [], "conditions": [], "routes": []}
    bodies: dict[str, Body] = {}
    for role in sorted(plan.component_parts):
        expected = plan.expected_labels(role)
        for instance in range(1, int(plan.geometries[role]["count"]) + 1):
            built = geometry.component(role, instance)
            defects = reconcile(expected, built, plan, role)
            if reconcile_all:
                for defect in defects:
                    if plan.geometries[role]["count"] > 1:
                        defect["instance"] = instance
                report["defects"] += defects
                report["failures"] += colour_failures(plan, built)
            elif defects and not any(item["part"] == role for item in report["defects"]):
                report["defects"].append(_defect(
                    "unreconciled", role, "part_%s does not match its leaves; its component round names how"
                    % role, component=role))
            bodies.update(keyed(plan, role, built, instance))
    if not report["defects"]:
        checked = _check(None, plan, geometry, bodies, nozzle)
        for key in ("conditions", "failures", "routes"):
            report[key] += checked[key]
    report["failures"] = list(dict.fromkeys(report["failures"]))
    return report


class CadGeometry:
    """The build123d backend: builds each Component from its own source,
    placed by its assembly_pose, and sweeps with check_motion's conditions."""

    def __init__(self, project: Path, counts: dict | None = None) -> None:
        import runpy

        self.project = Path(project).resolve()
        self.counts = dict(counts or {})
        scripts = Path(__file__).resolve().parents[2] / "cad" / "scripts"
        self.motion = runpy.run_path(str(scripts / "check_motion"), run_name="kit_tree_check_motion")
        if str(self.project) not in sys.path:
            sys.path.insert(0, str(self.project))
        try:
            from cadgen.booleans import serial_booleans

            serial_booleans()
        except ImportError:
            pass
        self.modules = {}

    def _module(self, role: str):
        if role not in self.modules:
            path = self.project / ("part_%s.step.py" % role)
            spec = importlib.util.spec_from_file_location("_kit_tree_" + role.replace("-", "_"), path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.modules[role] = module
        return self.modules[role]

    @staticmethod
    def _takes_instance(function) -> bool:
        try:
            return "instance" in inspect.signature(function).parameters
        except (TypeError, ValueError):
            return False

    def instances(self, role: str) -> list[int]:
        """Instance 1, and every other when the Component builds its
        instances differently (``gen_step(instance=n)``)."""

        module = self._module(role)
        if self._takes_instance(module.gen_step) or self._takes_instance(getattr(module, "bought_parts", None)):
            count = self._count(role)
            return list(range(1, count + 1))
        return [1]

    def _count(self, role: str) -> int:
        return int(self.counts.get(role, 1))

    def component(self, role: str, instance: int) -> list[Body]:
        module = self._module(role)
        place = getattr(module, "assembly_pose", None)
        if place is None:
            raise ValueError("part_%s.step.py defines no assembly_pose(shape, pose)" % role)
        bodies = []
        for name in ("gen_step", "bought_parts"):
            build = getattr(module, name, None)
            if build is None:
                continue
            shape = build(instance=instance) if self._takes_instance(build) else build()
            if shape is None:
                continue
            placed = place(shape, None, instance=instance) if self._takes_instance(place) else place(shape, None)
            bodies += self._bodies(placed)
        return bodies

    def _bodies(self, shape) -> list[Body]:
        from build123d import Location

        placed = self.motion["_placed_without_ancestry"]
        found = []

        def colour_of(node, inherited):
            value = getattr(node, "color", None)
            if value is None:
                return inherited
            channels = tuple(value)[:3]
            return "#%02x%02x%02x" % tuple(max(0, min(255, round(float(c) * 255))) for c in channels)

        def leaf_colours(node, inherited):
            children = list(getattr(node, "children", []) or [])
            mine = colour_of(node, inherited)
            if not children:
                return [mine]
            colours = []
            for child in children:
                colours += leaf_colours(child, mine)
            return colours

        def walk(node, pose, inherited):
            label = getattr(node, "label", "") or ""
            where = pose * node.location
            mine = colour_of(node, inherited)
            if PART_LABEL.match(label):
                shape = placed(node, where)
                found.append(Body(label, shape, solids=len(shape.solids()), colours=leaf_colours(node, inherited)))
                return
            children = list(getattr(node, "children", []) or [])
            if not children:
                shape = placed(node, where)
                if shape.solids():
                    found.append(Body(None, shape, solids=len(shape.solids())))
                return
            for child in children:
                walk(child, where, mine)

        walk(shape, Location(), None)
        return found

    def bounds(self, shapes) -> tuple:
        boxes = [shape.bounding_box() for shape in shapes]
        return ((min(b.min.X for b in boxes), min(b.min.Y for b in boxes), min(b.min.Z for b in boxes)),
                (max(b.max.X for b in boxes), max(b.max.Y for b in boxes), max(b.max.Z for b in boxes)))

    def _group(self, bodies):
        from build123d import Compound

        solids = [solid for body in bodies for solid in body.shape.solids()]
        return solids[0] if len(solids) == 1 else Compound(solids)

    def sweep(self, condition: dict, moving: list[Body], obstacles: list[Body]) -> dict:
        parts = {condition["inputs"]["moving_part"]: self._group(moving)}
        parts.update({body.key: body.shape for body in obstacles})
        condition = json.loads(json.dumps({key: value for key, value in condition.items() if key != "result"}))
        condition["inputs"]["obstacle_parts"] = [body.key for body in obstacles]
        return self.motion["run_condition"](condition, parts, 0)

    def nonparallel(self, moving, obstacles, direction) -> list[str]:
        """Every mating face pair at the seat that does not slide along
        ``direction``. A pair is a face of the input and a face of what it
        joins, of one kind and parallel to each other, within JOINT_GAP_MM:
        two flat faces (tab and slot walls, a seat and its stop) or two
        cylinders or cones on parallel axes (a peg and its bore, a pin and
        its lug). Flat pairs must face along or across the direction; round
        pairs must have their axis along it. A chamfer, a fillet or a body
        merely passing near another is no pair, so it is never judged."""

        from build123d import GeomType, Vector

        unit = Vector(*direction)
        limit = math.radians(PARALLEL_TOLERANCE_DEG)
        found = []
        targets = []
        for obstacle in obstacles:
            for face in obstacle.faces():
                read = _face_frame(face, GeomType)
                if read is not None:
                    targets.append((face, read, _grown(face.bounding_box(), JOINT_GAP_MM)))
        for shape in moving:
            for face in shape.faces():
                read = _face_frame(face, GeomType)
                if read is None:
                    continue
                kind, vector = read
                box = face.bounding_box()
                for other, (other_kind, other_vector), grown in targets:
                    if other_kind != kind or _apart(box, grown):
                        continue
                    if abs(_dot(vector, other_vector)) < math.cos(limit):
                        continue
                    try:
                        if face.distance_to(other) > JOINT_GAP_MM:
                            continue
                    except Exception:  # noqa: BLE001 - an unmeasurable pair is not judged
                        continue
                    angle = math.acos(min(1.0, abs(_dot(vector, (unit.X, unit.Y, unit.Z)))))
                    if kind == "plane" and limit < angle < math.pi / 2 - limit:
                        found.append("a flat joint face at %.0f deg to it near %s"
                                     % (math.degrees(angle), _point(face.center())))
                    elif kind == "round" and angle > limit:
                        found.append("a peg, bore or pin whose axis is %.0f deg off it near %s"
                                     % (math.degrees(angle), _point(face.center())))
                    break
        return list(dict.fromkeys(found))

    def route(self, points, size, obstacles) -> dict:
        from build123d import Compound, Plane, Pos, Solid, Vector

        radius = size / 2.0
        probes = [Pos(*point) * Solid.make_sphere(radius) for point in points]
        for start, end in zip(points, points[1:]):
            a, b = Vector(*start), Vector(*end)
            if (b - a).length > 0:
                probes.append(Solid.make_cylinder(radius, (b - a).length, Plane(origin=a, z_dir=b - a)))
        probe = Compound(probes)
        blocked = []
        for body in obstacles:
            try:
                volume = self.motion["overlap_volume"](probe, body.shape)
            except ValueError as error:
                return {"clear": False, "blocked_by": [], "detail": "unmeasured: %s" % error}
            if volume > OVERLAP_MM3:
                blocked.append({"obstacle": body.key, "overlapMm3": round(volume, 6)})
        return {"clear": not blocked, "blocked_by": blocked}


def _point(vector) -> str:
    return "(%.1f, %.1f, %.1f)" % (vector.X, vector.Y, vector.Z)


def _dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def _face_frame(face, GeomType):
    """``("plane", normal)`` or ``("round", axis)`` for a face that can mate,
    else None."""

    try:
        kind = face.geom_type
        if kind == GeomType.PLANE:
            normal = face.normal_at().normalized()
            return "plane", (normal.X, normal.Y, normal.Z)
        if kind in (GeomType.CYLINDER, GeomType.CONE):
            from OCP.BRepAdaptor import BRepAdaptor_Surface

            surface = BRepAdaptor_Surface(face.wrapped)
            axis = (surface.Cylinder() if kind == GeomType.CYLINDER else surface.Cone()).Axis().Direction()
            return "round", (axis.X(), axis.Y(), axis.Z())
    except Exception:  # noqa: BLE001 - an unreadable face is not judged
        return None
    return None


def _grown(box, margin):
    return ((box.min.X - margin, box.min.Y - margin, box.min.Z - margin),
            (box.max.X + margin, box.max.Y + margin, box.max.Z + margin))


def _apart(box, grown) -> bool:
    lo, hi = grown
    return (box.min.X > hi[0] or box.max.X < lo[0] or box.min.Y > hi[1] or box.max.Y < lo[1]
            or box.min.Z > hi[2] or box.max.Z < lo[2])


# ---------------------------------------------------------------------------
# reports, the pilot's defect ledger, and the command line


def summarise(report: dict) -> dict:
    report["verdict"] = "DEFECT" if report["defects"] else "FAIL" if report["failures"] else "PASS"
    return report


def defect_need(report: dict) -> str:
    """The need a tree defect stops the run with (ADR 0092 decision 10)."""

    shown = "; ".join("%s %s: %s" % (item["kind"], item["part"], item["detail"]) for item in report["defects"][:6])
    return ("Tree defect, reported to the owner, never repaired in the run (ADR 0092 decision 10): %s. "
            "Log it in the toy's TREE-ISSUES.md and correct the Design Contract's Assembly Tree or the "
            "Component's Part labels." % shown)


def defects_path(project: Path) -> Path:
    return Path(project) / "measure" / DEFECTS_FILE


def record_defects(project: Path, report: dict, digest: str) -> dict:
    """Write the defect ledger every later round refuses on."""

    record = {"tree_sha256": digest, "scope": report["scope"], "defects": report["defects"],
              "need": defect_need(report)}
    path = defects_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return record


def open_defects(project: Path, digest: str | None) -> dict | None:
    """The recorded tree defect of this tree, or None. A defect of an
    earlier tree (the owner since amended it) stops nothing."""

    try:
        record = json.loads(defects_path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or (digest is not None and record.get("tree_sha256") != digest):
        return None
    return record


def render(report: dict) -> str:
    lines = ["kit tree %s: %s, %d defect(s), %d failure(s), %d insertion sequence(s), %d lead route(s)"
             % (report["scope"], report["verdict"], len(report["defects"]), len(report["failures"]),
                len(report["conditions"]), len(report["routes"]))]
    lines += ["DEFECT %s %s: %s" % (item["kind"], item["part"], item["detail"]) for item in report["defects"]]
    lines += ["FAIL %s" % item for item in report["failures"]]
    if report["defects"]:
        lines.append("TREE DEFECT: stop. Do not change the model to hide it; the Workshop Manager stops the run "
                     "with this need: %s" % defect_need(report))
    return "\n".join(lines)


def run(project: Path, mode: str, role: str | None, nozzle: float, geometry=None) -> dict:
    kit = read_install(project)
    if kit is None:
        raise ValueError("the Assembly Tree is not installed: run kit_tree.py --install <cad-project> "
                         "--wish <run>/WISH.json")
    plan = Plan(kit)
    if geometry is None:
        geometry = CadGeometry(project, {key: int(item["count"]) for key, item in plan.geometries.items()})
    if mode == "component":
        if role not in plan.component_parts:
            raise ValueError("%s is no Component of the Assembly Tree" % role)
        report = check_component(plan, geometry, role, nozzle)
        report["defects"] = structure_defects(plan) + report["defects"]
    else:
        report = check_assembly(plan, geometry, nozzle, reconcile_all=(mode == "final"))
    report["tree_sha256"] = tree_digest(kit)
    report["kind"] = REPORT_KIND
    if mode == "final":
        report["leaves"] = {
            "printed": sorted(plan.printed), "bought": sorted(plan.bought), "pieces": sorted(plan.pieces),
        }
    return summarise(report)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", nargs="?", help="the CAD project")
    parser.add_argument("--install", metavar="CAD_PROJECT", help="install the sealed Assembly Tree")
    parser.add_argument("--wish", help="with --install: the run's WISH.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--component", metavar="GEOMETRY", help="the checks wholly inside one Component")
    mode.add_argument("--assembly", action="store_true", help="the checks across Components")
    mode.add_argument("--final", action="store_true", help="final verification: every check across Components, "
                      "every Component reconciled; writes measure/tree-report.json")
    parser.add_argument("--nozzle", type=float, default=0.4)
    parser.add_argument("--manifest", help="write the compiled check_motion conditions here")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    try:
        if args.install:
            if not args.wish:
                parser.error("--install needs --wish <run>/WISH.json")
            print(json.dumps(install(Path(args.install), Path(args.wish)), sort_keys=True))
            return EXIT_PASS
        if not args.project or not (args.component or args.assembly or args.final):
            parser.error("give a CAD project and one of --component, --assembly or --final")
        project = Path(args.project)
        selected = "component" if args.component else "final" if args.final else "assembly"
        report = run(project, selected, args.component.removeprefix("part_").removesuffix(".step.py")
                     if args.component else None, args.nozzle)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("kit_tree: %s" % error, file=sys.stderr)
        return EXIT_USAGE
    except Exception as error:  # noqa: BLE001 - a Component's own source failed to build or place
        # On stdout too, so the round's tree line names it.
        print("kit_tree: building the Components failed: %s: %s" % (type(error).__name__, error))
        print("kit_tree: building the Components failed: %s: %s" % (type(error).__name__, error), file=sys.stderr)
        return EXIT_FAIL
    manifest = {"conditions": report["conditions"]}
    if args.manifest:
        Path(args.manifest).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if args.final:
        # Beside the other verification evidence, which binds no review packet.
        (project / "measure").mkdir(exist_ok=True)
        (project / "measure" / REPORT_FILE).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                                                      encoding="utf-8")
        if report["defects"]:
            record_defects(project, report, report["tree_sha256"])
    print(render(report))
    if args.json:
        print(json.dumps(report, sort_keys=True))
    return EXIT_DEFECT if report["defects"] else EXIT_FAIL if report["failures"] else EXIT_PASS


# ---------------------------------------------------------------------------
# self-check: the pure parts, without CAD


def self_check() -> int:
    kit = {
        "kind": KIT_KIND, "schema_version": INSTALL_SCHEMA, "pieces": [],
        "geometries": [{"id": "box", "count": 1, "wall_min_mm": 1.2}],
        "catalogue": {"filaments": {"oak": {"hex": "#b5834f"}}, "bought_parts": {}},
        "assembly_tree": {
            "parts": [{"id": "A01-box", "name": "Box", "filament": "oak"},
                      {"id": "A02-peg", "name": "Peg", "filament": "oak"}],
            "steps": [{"id": "S01-pegs", "output": "Box", "count": 1, "joint": "peg-socket", "text": "Pegs in.",
                       "inputs": [{"id": "A01-box"}, {"id": "A02-peg", "count": 2, "direction": [0, 0, -1]}]}],
            "components": [{"geometry": "box", "parts": ["A01-box", "A02-peg"]}],
        },
    }
    plan = Plan(kit)
    problems = []
    if plan.expected_labels("box") != Counter({"A01-box": 1, "A02-peg#1": 1, "A02-peg#2": 1}):
        problems.append("expected labels")
    if travel_mm(((0, 0, 0), (1, 1, 1)), ((0, 0, 0), (1, 1, 1)), (0, 0, -1)) != 2.0:
        problems.append("travel")
    if plan.steps_in("box") != plan.steps or plan.steps_in(None):
        problems.append("scope")
    for problem in problems:
        print("kit_tree self-check failed: %s" % problem, file=sys.stderr)
    if not problems:
        print("kit_tree self-check: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
