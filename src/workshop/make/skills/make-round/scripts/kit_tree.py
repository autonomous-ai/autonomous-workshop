#!/usr/bin/env python3
"""The Assembly Tree gates of a schema 7 Design Contract (ADR 0092 decision 8).

    kit_tree.py --install <cad-project> --wish <run>/WISH.json
    kit_tree.py --install <cad-project> --contract CONTRACT.md   (outside a run)
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
``gen_step()``, and coloured :data:`BOUGHT_PART_HEX`, the reserved colour no
filament may take, so every render and STEP shows it is not printed (owner
decision Q29, 2026-10-23); it is never printed, so the print gates never see
it. When one
Component instance holds a Part more than once (four legs), the copies are
labelled ``<id>#1`` to ``<id>#4``. Every body is placed into the assembly by
the Component's own ``assembly_pose(shape, None)`` (``instance=n`` for the
n-th instance of a geometry whose count is above 1), which moves the shape as
a whole and keeps its labels. A labelled node is one body; an unlabelled node
is looked through; a solid reached without a Part label is an extra body.

The gates
---------
- **Reconciliation.** Every body, every Print Piece and every cited Bought
  Part matches exactly one leaf. Two kinds of mismatch differ (owner
  decision Q28, 2026-10-23):

  - A **contract tree defect**: the sealed tree itself does not hold
    together. A Print Piece or Bought Part the install cannot account for,
    a leaf that is an input of two steps, a Part in no step or no
    Component, and a leads step below the smallest Sub-assembly holding its
    lamps. In the pilot (ADR 0092 decision 10) it stops the run: it is
    recorded in ``measure/tree-defects.json`` and nothing repairs the tree.
  - A **labelling slip**: the tree holds together but the built bodies do
    not match it: a missing, extra or duplicated body (a label twice, one
    label on two solids, a body no leaf names, a Part of another
    Component). It is an ordinary failure the round's author repairs like
    a print gate; it records nothing and stops nothing.
- **Colour.** Every printed Part's body carries its filament's colour, so
  the review renders show the kit as it prints, and never
  :data:`BOUGHT_PART_HEX`; every Bought Part's body carries that reserved
  colour.
- **Insertion.** Each Assembly Step that joins (a joint of peg-socket,
  tab-slot, pin-hinge, foam-tape, glue, snap or paper) becomes one
  ``assembly_sequence`` of ``linear_motion_collision`` conditions
  (``check_motion``, ADR 0088), in Manual order. Its first input is the base
  and stays put. Every later input, each copy of it on its own, is swept from
  its seat back along its declared direction until it is wholly outside the
  bounds of the rest of the step's Sub-assembly, against only what is
  already assembled: the base and the inputs before it. Overlap above
  0.001 mm3 fails; seated contact at the seat is allowed. The sweep samples
  no coarser than the thinnest wall it could miss: the smaller of two print
  lines and the involved geometries' ``wall_min_mm`` (two print lines alone
  for a schema 9 contract, which states none). An input blocked only by
  an input of the same step that went in before it can go in only together
  with it: a simultaneous move, refused. Every joint the input engages at
  its seat must slide along the direction: each pair of mating faces (two
  parallel flat faces, or two cylinders or cones on parallel axes, within
  ``JOINT_GAP_MM``) faces along or across it, or has its axis along it. A
  pair at an angle is a non-parallel joint, unless it is a seat face (ADR
  0104 amendment 2026-11-19): the input's outward normal has n.d > 0 at
  every sample point, so it leads into its stop, and the input's sweep is
  clean. A press input (``press_mm``, same amendment) is held to its
  declared bite on both sides (ADR 0104 amendment 2026-11-27): the Part
  offset inward by it sweeps against its real obstacles, and the real Part
  against its obstacles, cropped to the sweep, offset inward by it, both
  at the same limit, so a rib thinner than twice the bite cannot vanish
  from the check. Where the kernel cannot offset a side whole, that side
  is offset only in windows round where it overlaps the other, each
  reaching past every overlap by more than the bite, which is exactly the
  whole offset there (ADR 0104 amendment 2026-11-26, press local offset).
  A side that cannot be shrunk at all is refused.
  A ``snap`` step (ADR 0104 amendment 2026-11-17) declares one pair, or a
  list of pairs, that may overlap on the way in: each snapping Part against
  its own catch, each overlap no deeper across the direction than that
  pair's ``catch_mm`` and inside its ``region_mm`` if given. Each pair must
  overlap somewhere on the way in (or it is no snap) and be clear at the
  seat. Every other pair, including a snapping Part against another pair's
  catch, is swept as above; each pass is recorded in the report's
  ``snaps``. A flat face of a pair's snapping Part wholly inside that pair's
  ``region_mm``, mating a face of its catch, is its barb's ramp: it is not
  judged as a non-parallel joint (it is recorded as ``ramp_faces``). With
  no ``region_mm`` nothing is exempt.
  When the moving group's solids cannot be fused into one material (the
  kernel's union is invalid or its volume inconsistent), each solid is
  swept on its own against every obstacle, each held to the overlap limit
  divided by the number of solids, so the sum can never pass what the fused
  sweep would refuse; each such fallback is recorded in ``fallbacks``.
- **Tilt hold** (ADR 0104 amendment 2026-11-19, rule i). Every input of a
  ``peg-socket``, ``tab-slot``, ``pin-hinge`` or ``snap`` step set down from
  above (its direction within 45 deg of -Z) is a unit, each copy on its own.
  Its host is every other body of the finished toy, so a part a later step
  clamps is held by it, and the toy's lowest level is the table a part may
  rest on. It runs over every step, Component-internal ones included, where
  the whole toy is built: in assembly rounds and final verification, never
  in a component round. ``CadGeometry.hold`` measures its height H above its
  bearing level and its engagement d below it; per way (+X, -X, +Y, -Y) the
  tip angle (its centre of mass over the bearing footprint's edge); lift (a
  0.3 mm lift that meets the host beyond its seat's own overlap: a snap or
  detent); and per way slide (a 0.3 mm push that does) and catch (the least
  of 1, 2 and 3 deg turned about that edge at which it does). It stays at a
  45 deg tray tilt when lift is held, or every way either tips no sooner
  than 45 deg or catches within 3 deg with slide held; only what that
  verdict needs is measured. A unit that does not stay is a failure; each
  is recorded in the report's ``holds``. Glue and tape hold by adhesive and
  are no unit.
- **Walls before the base** (same amendment, rule j). A printed plate Part
  (its smallest bounding extent at most 3.5 mm and under a third of the
  next) set on its own onto a Part it stands across (whose thin axis is
  another), within ``JOINT_GAP_MM``, is a wall of that base. A wall that
  touches two walls set on the same base before it, standing on opposite
  sides of it across its direction (each one's centre outside its extent)
  and each alongside it for at least half its length along the direction,
  goes in between parts already fixed: a failure naming the steps and walls, recorded in
  ``wall_orders``, telling the author to join the walls to each other first
  and then set them on the base. A Sub-assembly set on the base is no wall.
- **Lead routes.** A sphere of the lead's diameter (the lamp's catalogue
  ``lead diameter``) plus ``LEAD_CLEARANCE_MM`` is swept along each declared
  route; any printed body of the step's Sub-assembly in its way closes it.

Where each check runs: a step all of whose Parts belong to one Component is
checked in that Component's round (``--component``); a step across
Components in assembly rounds (``--assembly``) and in final verification
(``--final``, which also reconciles every Component and writes
``measure/tree-report.json`` for the host). The ``paper`` gate follows the same
split: :func:`paper_plan` says which Component round checks each Print Piece.

Final verification also writes ``measure/not-printed.json``: every Bought
Part body of the toy, ``<id>#n`` numbered across the whole toy, with its
catalogue id, so the STEP's reserved-colour bodies are listed as bought, not
printed (Q29). The host checks it, the receipt carries it and Release ships
it beside the STEP files.

Exit status: 0 pass, 1 a repairable failure (a labelling slip included), 3 a
contract tree defect, 2 bad usage.
The last stdout line is the JSON report with ``--json``.
"""

from __future__ import annotations
import os as _cadthreads_os, runpy as _cadthreads_runpy  # noqa: E401,E402
# Before numpy, build123d or OCP load: this process and every tool it starts get one
# BLAS/OpenMP/OCCT thread unless the caller set one (cad/scripts/cadthreads.py).
_cadthreads_path = _cadthreads_os.path.join(_cadthreads_os.path.dirname(_cadthreads_os.path.abspath(__file__)), "..", "..", "cad", "scripts", "cadthreads.py")
# A copy made without its helper runs as before, unpinned.
_cadthreads = _cadthreads_runpy.run_path(_cadthreads_path) if _cadthreads_os.path.isfile(_cadthreads_path) else None
if _cadthreads is not None:
    _cadthreads["pin"](occ=True)

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
# The pilot's ledger of contract tree defects (ADR 0092 decision 10), under measure/.
DEFECTS_FILE = "tree-defects.json"
# Final verification's list of every Bought Part body (Q29), under measure/.
NOT_PRINTED_FILE = "not-printed.json"
NOT_PRINTED_KIND = "kit-not-printed"
# The one colour every Bought Part body carries in every STEP and render, and
# no filament may take: a clearly artificial magenta, never a stocked spool
# (owner decision Q29, 2026-10-23). The host's catalogue validator holds the
# same value (workshop.wish.catalogues.BOUGHT_PART_HEX); a test keeps them one.
BOUGHT_PART_HEX = "#ff00ff"

JOINS = ("peg-socket", "tab-slot", "pin-hinge", "foam-tape", "glue", "snap")
SNAP = "snap"
PAPER = "paper"
LEADS = "leads"
SWEPT = JOINS + (PAPER,)

OVERLAP_MM3 = 0.001          # contact is not collision (check_motion's default)
OUTSIDE_MARGIN_MM = 1.0      # how far past the Sub-assembly's bounds a sweep starts
LEAD_CLEARANCE_MM = 0.4      # 0.2 mm all round the lead: a cadfits slip fit
# A snap's measured depth may exceed its declared catch by no more than this
# (an OCCT bounding box's float noise, not a design allowance).
SNAP_TOLERANCE_MM = 1e-3
JOINT_GAP_MM = 0.3           # a face this close to what it joins is a joint face
# Press local offset (ADR 0104 amendment 2026-11-26): where the kernel can
# offset a side of a press (the input, or an obstacle) not whole, it is
# offset only inside windows round where it overlaps the other side. A
# window reaches past every overlap by more than the press, so the offset of
# its cut faces can never reach an overlap: the window's offset is exactly
# the whole offset there. These are the margins tried beyond the press, in
# order, and the longest side of one window before it is split into tiles.
PRESS_LOCAL_MARGINS_MM = (0.3, 0.15, 0.6)
PRESS_LOCAL_TILE_MM = 8.0
PRESS_OFFSET_SECONDS = 120   # a sharp join still running after this is refused (#392)
PRESS_INSIDE_MM3 = 1e-5     # a shrink holding more outside its body is not taken (#392)
# How long one tree check may take: a Component's tree, an assembly's or
# the final one. Its time grows with its insertions, each a sweep, and a
# press input's more, held on both sides by shrunk solids (#392): Kyoto's
# 188 insertions, 128 of them presses, took 13,900 s at one thread on
# main. TREE_MIN_S for any scope, plus these for each insertion and each
# press insertion, give it 32,280 s, about 2.3 times that. Miami's
# heaviest tree (44, 38 presses: 792 s) gets 11,760 s. The host's batch
# deadlines (``seeded_batch``) mirror them.
TREE_MIN_S = 3600.0
TREE_INSERTION_S = 30.0
TREE_PRESS_S = 180.0
# Where the kernel cannot offset a window's cut either, it is shrunk by
# booleans (CadGeometry.eroded), checked on this many grid points a side.
PRESS_ERODE_SAMPLES = 6
# Directions within these cosines of one already taken are skipped: flat
# faces' normals all count; a curved face's sampled normals within 10 deg
# of one taken add nothing but booleans. Fewer directions only keep more.
PRESS_ERODE_SAME = 1.0 - 1e-9
PRESS_ERODE_CURVED = math.cos(math.radians(10.0))
PARALLEL_TOLERANCE_DEG = 2.0
PRINT_LINES = 2              # the thinnest printable wall, in lines
# The tilt hold (ADR 0104 amendment 2026-11-19, rule i): a unit set down by a
# mechanical joint stays seated with the tray tilted this far, any way.
HOLD_TILT_DEG = 45.0
HELD_JOINTS = ("peg-socket", "tab-slot", "pin-hinge", "snap")   # glue and tape hold by adhesive
HOLD_CATCH_DEG = 3.0         # a joint that binds by this tilt catches the unit
HOLD_CATCH_SAMPLES_DEG = (1.0, 2.0, 3.0)   # ascending, the last HOLD_CATCH_DEG
HOLD_PUSH_MM = 0.3           # a sideways push or lift this far that meets the host is held
HOLD_HIT_MM3 = 0.002         # overlap beyond the seat's own that counts as meeting the host
BEARING_GAP_MM = 0.06        # a downward face this close to the host bears on it
BEARING_NZ = -0.5            # a bearing face's normal points down within 60 deg
WAYS = ("+X", "-X", "+Y", "-Y")
# Walls before the base (same amendment, rule j): a plate is at most this thick.
WALL_PLATE_MM = 3.5

DEFECT = "defect"
FAILURE = "failure"
PART_LABEL = re.compile(r"^([A-LO-RT-Z][0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*)(?:#([1-9][0-9]*))?$")
EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_DEFECT = 0, 1, 2, 3


# ---------------------------------------------------------------------------
# install


def has_assembly_tree(contract) -> bool:
    """Whether a sealed Design Contract is a kit: schema 7 always has an
    Assembly Tree, a schema 8 contract when it is a kit (ADR 0093). The
    host's workshop.make.kit_tree holds the same rule."""

    if not isinstance(contract, dict):
        return False
    schema = contract.get("schema_version")
    return type(schema) is int and schema >= TREE_SCHEMA_VERSION and isinstance(contract.get("assembly_tree"), dict)


def install_document(contract: dict, catalogue: dict | None) -> dict:
    """The exact install a sealed kit contract (schema 7, or a schema 8 kit)
    and its catalogue snapshot give. The host builds the same document to
    check Make."""

    if not has_assembly_tree(contract):
        raise ValueError("the sealed Design Contract has no Assembly Tree: it is not a kit")
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


def contract_catalogue(text: str) -> dict:
    """The catalogue snapshot a run would seal for this contract text: the
    Workshop parser's own ``kit_catalogue()`` over the owner's catalogues,
    so an install outside a run carries the colours and sizes a run's does."""

    from workshop.wish.design_contract import parse_design_contract  # the Workshop package

    from workshop.errors import WorkshopError

    try:
        return parse_design_contract(text).kit_catalogue() or {}
    except WorkshopError as error:
        raise ValueError(str(error)) from None


def install_contract(project: Path, contract_path: Path) -> dict:
    """Write ``tree/kit.json`` from a Design Contract file outside a run (the
    Contract Proof, ADR 0096 decision 1b): the same document a sealed Wish
    gives, its catalogue snapshot taken by the Workshop contract parser.
    Refuses an existing install with other bytes."""

    project = Path(project)
    if not project.is_dir():
        raise ValueError("%s: not a CAD project directory" % project)
    text = Path(contract_path).read_text(encoding="utf-8")
    match = re.search(r"```design-contract\s*\n(.*?)```", text, re.DOTALL)
    try:
        block = json.loads(match.group(1) if match else text)
    except ValueError as exc:
        raise ValueError("%s holds no design-contract JSON block: %s" % (contract_path, exc)) from None
    if not isinstance(block, dict) or not block.get("assembly_tree"):
        raise ValueError("%s: the Design Contract has no Assembly Tree" % contract_path)
    document = install_document(block, contract_catalogue(text))
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
        # A schema 9 geometry states no wall_min_mm (ADR 0094): two print lines.
        walls = [float(self.geometries[g]["wall_min_mm"]) for g in geometries
                 if g in self.geometries and "wall_min_mm" in self.geometries[g]]
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
    """Missing, extra and duplicated bodies of one Component instance: each a
    labelling slip (Q28), repaired in the next round, never a tree defect."""

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


def slip_failure(slip: dict) -> str:
    """A labelling slip as the failure line its round's author repairs."""

    where = " (instance %d)" % slip["instance"] if "instance" in slip else ""
    return "labelling slip%s: %s %s: %s; rebuild or relabel the body to match the tree" % (
        where, slip["kind"], slip["part"], slip["detail"])


def colour_failures(plan: Plan, bodies: list[Body]) -> list[str]:
    """Each printed Part in its filament's colour and never the reserved
    Bought Part colour; each Bought Part in the reserved colour (Q29)."""

    failures = []
    filaments = plan.catalogue.get("filaments") or {}
    for body in bodies:
        match = PART_LABEL.match(body.label or "")
        part = plan.parts.get(match.group(1)) if match else None
        if part is None:
            continue
        if "bought" in part:
            wrong = sorted({colour or "uncoloured" for colour in body.colours
                            if not _same_colour(colour, BOUGHT_PART_HEX)})
            if not body.colours or wrong:
                failures.append("%s is a Bought Part in %s, not the reserved not-printed colour %s: colour it %s"
                                % (body.label, ", ".join(wrong) or "uncoloured", BOUGHT_PART_HEX,
                                   BOUGHT_PART_HEX))
            continue
        if "filament" not in part:
            continue
        want = (filaments.get(part["filament"]) or {}).get("hex")
        if want is None:
            continue
        if any(_same_colour(colour, BOUGHT_PART_HEX) for colour in body.colours):
            failures.append("%s is a printed Part in %s, the reserved colour of Bought Parts: colour it its "
                            "filament %s (%s)" % (body.label, BOUGHT_PART_HEX, part["filament"], want))
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

    report = {"conditions": [], "failures": [], "routes": [], "snaps": [], "presses": [], "seats": [],
              "holds": [], "wall_orders": [], "_placements": []}
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
    _wall_order(plan, geometry, report.pop("_placements"), report)
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
        snaps = _snaps_of(plan, item, entry)
        for j in range((k - 1) * per + 1, k * per + 1):
            moving = _bodies_of(plan, bodies, entry["id"], j)
            if not moving:
                continue   # paper: the paper gate checks where it lands
            name = "%s#%d" % (entry["id"], j)
            others = [body for body in whole if body not in moving]
            if not assembled or not others:
                for snap in snaps:
                    report["failures"].append(
                        "%s: %s declares a snap into %s but nothing is assembled for it to pass"
                        % (step, name, snap["catch"]))
                assembled += [(entry["id"], body) for body in moving]
                continue
            travel = travel_mm(geometry.bounds([b.shape for b in moving]),
                               geometry.bounds([b.shape for b in others]), direction)
            steps = max(1, math.ceil(travel / wall - 1e-9))
            # A declared snap's catch is swept on its own (_snap_pass); every
            # other body already there blocks as for any join.
            catches = {snap["catch"] for snap in snaps}
            caught = [body for _, body in assembled if _leaf(body) in catches]
            blocking = [(source, body) for source, body in assembled if body not in caught]
            condition = {
                "id": "%s.%s" % (step, name) if plan.totals[step] == 1 else "%s#%d.%s" % (step, k, name),
                "check": "linear_motion_collision",
                "expect": "clear",
                "description": "%s goes in alone along %s" % (name, list(entry["direction"])),
                "inputs": {"moving_part": name, "obstacle_parts": [body.key for _, body in blocking],
                           "translation": [round(-c * travel, 6) for c in direction],
                           "steps": steps, "allow_seated_contact": True},
                "thresholds": {"maxOverlapMm3": OVERLAP_MM3, "maxStepMm": round(wall, 6)},
            }
            press = entry.get("press_mm")
            swept = moving
            obstacles = [body for _, body in blocking]
            other_obstacles = None
            if press:
                # A press input (ADR 0104 amendment 2026-11-19): its ribs bite
                # the declared depth. Both sides are held to it (amendment
                # 2026-11-27, #392): the Part offset inward by the press
                # sweeps against its real obstacles, and the real Part
                # against its obstacles offset inward by the press, both at
                # the unchanged overlap limit. So every overlap lies within
                # the press of both bodies' faces: a rib thinner than twice
                # the press, which one side's offset removes whole, still
                # fails by its depth in the other. Where the kernel cannot
                # offset a side whole, it is offset only in windows round
                # its overlaps (amendment 2026-11-26). A side it cannot
                # shrink at all is refused, never swept as it is.
                condition["inputs"]["press_mm"] = press
                condition["description"] += ", offset inward by its %.3g mm press" % press
                swept, error = geometry.pressed(moving, press)
                offset_side = "input"
                if error is not None and blocking and hasattr(geometry, "pressed_local"):
                    local, why = geometry.pressed_local(condition, moving, obstacles, press)
                    if local is None:
                        error = "%s; nor in windows round its overlaps: %s" % (error, why)
                    else:
                        swept, error, offset_side = local, None, "local"
                        condition["inputs"]["press_offset"] = "local"
                        condition["description"] = condition["description"].replace(
                            ", offset inward by its", ", offset inward round its overlaps by its")
                obstacle_side = None
                if error is None and blocking and hasattr(geometry, "shrunk_obstacles"):
                    other_obstacles, obstacle_side, why = geometry.shrunk_obstacles(
                        condition, moving, obstacles, press)
                    if other_obstacles is None:
                        swept, error = None, "its obstacles cannot be offset inward by it either: %s" % why
                report["presses"].append({"id": condition["id"], "step": step, "input": name, "press_mm": press,
                                          "offset": offset_side, "obstacles": obstacle_side,
                                          "verdict": "PASS" if error is None else "FAIL"})
                if error is not None:
                    swept = None
                    report["failures"].append(
                        "%s: %s is a press input, but its Part cannot be offset inward by its %.3g mm press "
                        "(%s): refused" % (step, name, press, error))
            clean = False
            if blocking and swept is not None:
                sequence["inputs"]["steps"].append(condition)
                result = geometry.sweep(condition, swept, obstacles)
                condition["result"] = {key: result.get(key) for key in ("status", "detail", "obstacle", "overlapMm3")
                                       if key in result}
                clean = result.get("status") == "pass"
                if not clean:
                    _blocked(geometry, step, name, entry, base, condition, result, swept, blocking, report)
                elif other_obstacles is not None:
                    # The other side of the press (#392): the real Part
                    # against its obstacles offset inward by the press.
                    other = json.loads(json.dumps({key: value for key, value in condition.items()
                                                   if key != "result"}))
                    other["id"] = condition["id"] + ".obstacles-pressed"
                    other["description"] = "%s goes in alone along %s against its obstacles offset inward by " \
                                           "its %.3g mm press" % (name, list(entry["direction"]), press)
                    other["inputs"].pop("press_windows", None)
                    other["inputs"].pop("press_eroded", None)
                    other["inputs"]["press_offset"] = "obstacles" if obstacle_side == "offset" else "obstacles-local"
                    sequence["inputs"]["steps"].append(other)
                    second = geometry.sweep(other, moving, other_obstacles)
                    other["result"] = {key: second.get(key) for key in ("status", "detail", "obstacle", "overlapMm3")
                                       if key in second}
                    clean = second.get("status") == "pass"
                    if not clean:
                        report["failures"].append(
                            ("%s: %s cannot go in alone along %s against its obstacles offset inward by its "
                             "%.3g mm press: it bites deeper than its press into them: %s"
                             if second.get("status") == "fail" else
                             "%s: %s along %s against its obstacles offset inward by its %.3g mm press "
                             "cannot be checked: %s: refused")
                            % (step, name, list(entry["direction"]), press, second.get("detail")))
                if press:
                    report["presses"][-1]["verdict"] = "PASS" if clean else "FAIL"
            if snaps:
                _snap_pass(geometry, step, name, entry, snaps, condition, moving, caught, report)
            ramps = _ramps(snaps, moving, caught)
            extra = {"exempt": ramps} if ramps else {}
            # A seat face (ADR 0104 amendment 2026-11-19) is accepted only
            # when the sweep is clean.
            seats = [] if clean else None
            for face in geometry.nonparallel([b.shape for b in moving], [b.shape for _, b in assembled],
                                             direction, seats=seats, **extra):
                report["failures"].append("%s: %s engages a joint that is not parallel to its direction %s: %s"
                                          % (step, name, list(entry["direction"]), face))
            for face in seats or ():
                report["seats"].append({"step": step, "input": name, "face": face})
            if entry["id"] in plan.printed and len(moving) == 1:
                report["_placements"].append({"step": step, "input": name, "body": moving[0],
                                              "direction": direction,
                                              "before": [b for _, b in assembled if _leaf(b) in plan.printed]})
            for ramp in ramps:
                for record in report["snaps"]:
                    if (record["step"], record["input"], record["part"], record["catch"]) == (
                            step, name, ramp["pair"]["part"], ramp["pair"]["catch"]):
                        record.setdefault("ramp_faces", [])
                        record["ramp_faces"] += [f for f in ramp["faces"] if f not in record["ramp_faces"]]
            assembled += [(entry["id"], body) for body in moving]


def _holds(plan: Plan, geometry, bodies: dict[str, Body], report: dict) -> None:
    """The tilt hold of the finished toy (ADR 0104 amendment 2026-11-19,
    rule i). A unit is each copy of an input set down from above (its
    direction within HOLD_TILT_DEG of -Z) by a mechanical joint, in every
    step of the tree; its host is every other body of the toy, so a part a
    later step clamps is held by it, and the toy's lowest level is the
    table a part may rest on. It runs where the whole toy is built:
    assembly rounds and final verification. A backend without ``hold`` (a
    test fake) measures nothing."""

    if getattr(geometry, "hold", None) is None:
        return
    limit = -math.cos(math.radians(HOLD_TILT_DEG))
    # The table the toy stands on: a part resting on it bears on it.
    floor = geometry.bounds([body.shape for body in bodies.values()])[0][2] if bodies else None
    for item in plan.steps:
        if item.get("joint") not in HELD_JOINTS:
            continue
        step = item["id"]
        for entry in plan.inputs[step][1:]:
            if _unit(entry["direction"])[2] > limit:
                continue
            for j in range(1, plan.totals.get(entry["id"], 0) + 1):
                moving = _bodies_of(plan, bodies, entry["id"], j)
                if not moving:
                    continue
                keys = {body.key for body in moving}
                host = [body for key, body in sorted(bodies.items()) if key not in keys]
                if host:
                    _hold(geometry, step, "%s#%d" % (entry["id"], j), moving, host, floor, report)


def _hold(geometry, step, name, moving, host, floor, report) -> None:
    """One unit's tilt hold: it stays seated with the tray tilted 45 deg in
    any direction."""

    record = {"step": step, "input": name,
              **geometry.hold([b.shape for b in moving], [b.shape for b in host], floor)}
    record["stays_45"] = hold_stays(record)
    record["verdict"] = "PASS" if record["stays_45"] else "FAIL"
    report["holds"].append(record)
    if not record["stays_45"]:
        falls = [way for way in WAYS if not _way_holds(record, way)]
        report["failures"].append(
            "%s: %s does not stay seated with the tray tilted %g deg: H %.1f mm above its bearing level, d %.1f "
            "mm engaged below it, no lift hold; %s. Engage it deeper, add a snap or detent, or widen its "
            "footprint (owner rule: every freestanding part survives a knock)" % (
                step, name, HOLD_TILT_DEG, record["H"], record["d"],
                "; ".join(_way_text(record, way) for way in falls)))


def _way_text(record: dict, way: str) -> str:
    text = "toward %s it tips at %g deg" % (way, record["tip"][way])
    if not record["slide"][way]:
        return text + " and slides free"
    return text + ", and its joint does not catch it by %g deg" % HOLD_CATCH_DEG


def hold_stays(record: dict) -> bool:
    """Whether a measured unit stays at the tilt: held down against a lift
    (a snap or detent), or every way either tips no sooner than the tilt or
    catches within HOLD_CATCH_DEG and is held against sliding."""

    return bool(record["lift"]) or all(_way_holds(record, way) for way in WAYS)


def _way_holds(record: dict, way: str) -> bool:
    if record["lift"] or record["tip"][way] >= HOLD_TILT_DEG:
        return True
    catch = record["catch"][way]
    return catch is not None and catch <= HOLD_CATCH_DEG and bool(record["slide"][way])


def _plate_axis(geometry, shape) -> int | None:
    """The thin axis of a plate (its smallest bounding extent at most
    WALL_PLATE_MM and under a third of the next), else None."""

    lo, hi = geometry.bounds([shape])
    size = [hi[a] - lo[a] for a in range(3)]
    order = sorted(range(3), key=lambda a: size[a])
    if size[order[0]] <= WALL_PLATE_MM and size[order[1]] >= 3 * size[order[0]]:
        return order[0]
    return None


def _thin_axis(geometry, shape) -> int:
    lo, hi = geometry.bounds([shape])
    return min(range(3), key=lambda a: hi[a] - lo[a])


def _near(geometry, a, b) -> bool:
    lo, hi = geometry.bounds([a])
    other = geometry.bounds([b])
    return all(lo[x] - JOINT_GAP_MM <= other[1][x] and other[0][x] - JOINT_GAP_MM <= hi[x] for x in range(3))


def _flanked(geometry, wall, earlier) -> bool:
    """Whether a wall goes in between two walls already fixed: two of the
    earlier walls it touches stand on opposite sides of it across its
    direction, each one's centre outside the wall's own extent on that axis,
    and each runs alongside it for at least half its length along the
    direction. A plate set over the tops of walls spans them, so it is not
    between them."""

    lo, hi = geometry.bounds([wall["body"].shape])
    along = max(range(3), key=lambda a: abs(wall["direction"][a]))
    length = hi[along] - lo[along]
    sides = []
    for other in earlier:
        olo, ohi = geometry.bounds([other["body"].shape])
        if min(hi[along], ohi[along]) - max(lo[along], olo[along]) < length / 2:
            continue
        centre = [(olo[a] + ohi[a]) / 2 for a in range(3)]
        sides.append([-1 if centre[a] < lo[a] else 1 if centre[a] > hi[a] else 0 for a in range(3)])
    return any(a[axis] * b[axis] < 0 for n, a in enumerate(sides) for b in sides[n + 1:]
               for axis in range(3) if axis != along)


def _wall_order(plan, geometry, placements, report) -> None:
    """Walls before the base (ADR 0104 amendment 2026-11-19, rule j): a
    plate Part set on its own onto a base it stands across, touching two
    walls set on that same base before it that flank it (``_flanked``),
    goes in between two parts already fixed. The walls that meet each other are joined to each other
    first, as a Sub-assembly, and then set on the base. A backend without
    ``touching`` (a test fake) measures nothing."""

    touching = getattr(geometry, "touching", None)
    if touching is None:
        return
    walls: dict[str, list[dict]] = {}
    anchors: dict[str, Body] = {}
    for placed in placements:
        axis = _plate_axis(geometry, placed["body"].shape)
        if axis is None:
            continue
        for anchor in placed["before"]:
            if _thin_axis(geometry, anchor.shape) == axis or not _near(geometry, placed["body"].shape, anchor.shape):
                continue
            if touching(placed["body"].shape, anchor.shape, JOINT_GAP_MM):
                walls.setdefault(anchor.key, []).append(placed)
                anchors[anchor.key] = anchor
    for key, group in walls.items():
        meets = {}
        for i, later in enumerate(group):
            meets[i] = [j for j, earlier in enumerate(group[:i])
                        if _near(geometry, later["body"].shape, earlier["body"].shape)
                        and touching(later["body"].shape, earlier["body"].shape, JOINT_GAP_MM)]
        between = [i for i, earlier in meets.items()
                   if _flanked(geometry, group[i], [group[j] for j in earlier])]
        if not between:
            continue
        # Every wall joined to a wall that goes in between, by contact.
        chosen, stack = set(), list(between)
        while stack:
            i = stack.pop()
            if i in chosen:
                continue
            chosen.add(i)
            stack += meets[i] + [j for j, earlier in meets.items() if i in earlier]
        members = [group[i] for i in sorted(chosen)]
        record = {"base": key, "steps": list(dict.fromkeys(m["step"] for m in members)),
                  "walls": [m["input"] for m in members],
                  "between": [group[i]["input"] for i in between], "verdict": "FAIL"}
        report["wall_orders"].append(record)
        report["failures"].append(
            "%s: %s are each set on %s one at a time, and %s goes in between walls already fixed: join these "
            "walls to each other first, then set them on %s (owner rule: build sub-assemblies first)"
            % (", ".join(record["steps"]), ", ".join(record["walls"]), key, ", ".join(record["between"]), key))


def _blocked(geometry, step, name, entry, base, condition, result, moving, assembled, report) -> None:
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


def _triple(point) -> str:
    return "(%.2f, %.2f, %.2f)" % tuple(point)


def _leaf(body) -> str:
    return body.key.rsplit("#", 1)[0]


def _snaps_of(plan, item, entry) -> list[dict]:
    """The step's declared snap pairs whose snapping Part is a leaf of
    ``entry``: ``snap`` is one pair or a list of them."""

    value = item.get("snap") if item.get("joint") == SNAP else None
    pairs = value if isinstance(value, list) else [value] if value else []
    leaves = plan.leaves_under(entry["id"])
    return [snap for snap in pairs if snap["part"] in leaves]


def _ramps(snaps, moving, caught) -> list[dict]:
    """Each declared pair with a ``region_mm``, by body: the snapping Part's
    shape, its catch's shape and the region its ramp faces must lie wholly
    inside to be exempt from the non-parallel joint check."""

    found = []
    for snap in snaps:
        region = snap.get("region_mm")
        if region is None:
            continue
        for body in moving:
            if _leaf(body) != snap["part"]:
                continue
            for other in caught:
                if _leaf(other) == snap["catch"]:
                    found.append({"part": body.shape, "catch": other.shape, "region": region,
                                  "tolerance": SNAP_TOLERANCE_MM, "pair": snap, "faces": []})
    return found


def _snap_pass(geometry, step, name, entry, snaps, condition, moving, caught, report) -> None:
    """The declared snap pairs of one input (ADR 0104 amendment 2026-11-17):
    every moving body stays clear of every catch it is not declared to snap
    into; each pair's snapping Part may overlap its own catch on its way in,
    each overlap no deeper across the direction than the pair's catch and
    inside its barb region; at its seat it is clear; and it does overlap, or
    it is no snap."""

    label = "%s: %s" % (step, name)
    declared = {(snap["part"], snap["catch"]) for snap in snaps}
    groups: dict[tuple, tuple[list, list]] = {}
    for body in moving:
        barred = [other for other in caught if (_leaf(body), _leaf(other)) not in declared]
        if barred:
            groups.setdefault(tuple(other.key for other in barred), (barred, []))[1].append(body)
    for n, (barred, bodies) in enumerate(groups.values()):
        clear = {**condition, "id": condition["id"] + (".catch" if len(groups) == 1 else ".catch%d" % (n + 1)),
                 "description": "%s but no Part touches a catch it does not snap into" % name,
                 "inputs": {**condition["inputs"], "obstacle_parts": [other.key for other in barred]}}
        result = geometry.sweep(clear, bodies, barred)
        if result.get("status") != "pass":
            report["failures"].append("%s cannot go in alone along %s: %s"
                                      % (label, list(entry["direction"]), result.get("detail")))
    if sum(1 for c in entry["direction"] if c != 0) != 1:
        report["failures"].append("%s snaps in along %s, not along one axis of the assembly frame"
                                  % (label, list(entry["direction"])))
        return
    for n, snap in enumerate(snaps):
        suffix = ".snap" if len(snaps) == 1 else ".snap%d" % (n + 1)
        _snap_pair(geometry, step, name, entry, snap, suffix, condition, moving, caught, report)


def _snap_pair(geometry, step, name, entry, snap, suffix, condition, moving, caught, report) -> None:
    held = [body for body in moving if _leaf(body) == snap["part"]]
    mine = [body for body in caught if _leaf(body) == snap["catch"]]
    label = "%s: %s" % (step, name)
    if not mine or not held:
        report["failures"].append("%s declares a snap of %s into %s, but %s is not there to pass"
                                  % (label, snap["part"], snap["catch"],
                                     snap["catch"] if not mine else snap["part"]))
        return
    axis = max(range(3), key=lambda a: abs(entry["direction"][a]))
    across = [a for a in range(3) if a != axis]
    passing = {**condition, "id": condition["id"] + suffix, "check": "snap_catch",
               "description": "%s passes %s no deeper than its %.3g mm catch" % (held[0].key, snap["catch"],
                                                                              snap["catch_mm"]),
               "inputs": {**condition["inputs"], "moving_part": ", ".join(body.key for body in held),
                          "obstacle_parts": [body.key for body in mine], "allow_seated_contact": False}}
    samples = geometry.snap_overlaps(passing, held, mine)
    total = condition["inputs"]["steps"]
    seated = sum(item["volume"] for item in samples if item["step"] == 0)
    on_way = [item for item in samples if item["step"] > 0]
    region = snap.get("region_mm")
    depth, worst, failures = 0.0, 0.0, []
    for item in on_way:
        lo, hi = item["bounds"]
        deep = min(hi[a] - lo[a] for a in across)
        depth, worst = max(depth, deep), max(worst, item["volume"])
        if deep > snap["catch_mm"] + SNAP_TOLERANCE_MM:
            failures.append("%s passes %s %.3f mm deep at step %d/%d, deeper than its declared %.3g mm catch"
                            % (label, item["catch"], deep, item["step"], total, snap["catch_mm"]))
        elif region is not None and not _inside(lo, hi, region):
            failures.append("%s overlaps %s outside its declared barb region %s at step %d/%d: %s to %s"
                            % (label, item["catch"], region, item["step"], total,
                               _triple(lo), _triple(hi)))
    if seated > OVERLAP_MM3:
        failures.insert(0, "%s is not clear of %s at its seat (%.4g mm3): a snap's barb sits clear under "
                           "its catch" % (label, snap["catch"], seated))
    if not on_way:
        failures.append("%s declares a snap into %s but never overlaps it on its way in: no barb passes "
                        "a catch, so declare the joint it is" % (label, snap["catch"]))
    report["failures"] += list(dict.fromkeys(failures))
    report["snaps"].append({
        "id": passing["id"], "step": step, "input": name, "part": snap["part"], "catch": snap["catch"],
        "catch_mm": snap["catch_mm"], "region_mm": region, "samples": total,
        "overlapping_samples": len({item["step"] for item in on_way}),
        "max_depth_mm": round(depth, 6), "max_overlap_mm3": round(worst, 6), "seated_mm3": round(seated, 6),
        "verdict": "FAIL" if failures else "PASS",
    })


def _ramp_of(exempt, shape, owner, box):
    """The declared pair whose ramp this face is: on its snapping Part,
    mating its catch, its bounding box wholly inside its region."""

    for ramp in exempt:
        if ramp["part"] is shape and ramp["catch"] is owner and _inside(
                (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z),
                ramp["region"], ramp["tolerance"]):
            return ramp
    return None


def _inside(lo, hi, region, tolerance=SNAP_TOLERANCE_MM) -> bool:
    return all(region[0][a] - tolerance <= lo[a] and hi[a] <= region[1][a] + tolerance for a in range(3))


SEAT_SAMPLES = (0.05, 0.275, 0.5, 0.725, 0.95)


def _seat_face(face, unit) -> bool:
    """Whether a face of the moving input leads into its stop: its outward
    normal has n.d > 0 at every sample point of its parameter range (ADR
    0104 amendment 2026-11-19). A point the kernel cannot read is no seat."""

    try:
        for u in SEAT_SAMPLES:
            for v in SEAT_SAMPLES:
                if face.normal_at(face.position_at(u, v)).dot(unit) <= 0:
                    return False
    except Exception:  # noqa: BLE001 - an unreadable face is judged as before
        return False
    return True


ON_FACE_MM = 1e-3


def _faces_each_other(face, other) -> bool:
    """Whether a face of the moving input and a face of what it joins face
    each other across the gap (ADR 0104 amendment 2026-11-19, rule h): some
    sample point of ``face``, within JOINT_GAP_MM of ``other``, has its foot
    on ``other``'s surface inside ``other``, and the two outward normals there
    are opposed. Two faces facing the same way (one flush surface across a
    seam) or meeting only along an edge are no joint. A pair the kernel cannot
    read is judged a joint, as before."""

    try:
        from OCP.BRep import BRep_Tool
        from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCP.gp import gp_Pnt
        from build123d import Vector

        surface = BRep_Tool.Surface_s(other.wrapped)
        for u in SEAT_SAMPLES:
            for v in SEAT_SAMPLES:
                point = face.position_at(u, v)
                if face.distance_to(point) > ON_FACE_MM or other.distance_to(point) > JOINT_GAP_MM:
                    continue
                projection = GeomAPI_ProjectPointOnSurf(gp_Pnt(point.X, point.Y, point.Z), surface)
                if projection.NbPoints() == 0:
                    continue
                near = projection.NearestPoint()
                foot = Vector(near.X(), near.Y(), near.Z())
                if other.distance_to(foot) > ON_FACE_MM:
                    continue
                if face.normal_at(point).dot(other.normal_at(foot)) < 0:
                    return True
    except Exception:  # noqa: BLE001 - an unreadable pair is judged as before
        return True
    return False


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


def tree_load(plan: Plan, scope: str | None) -> dict:
    """``{"insertions": n, "presses": m}``: how many inputs the tree check
    of ``scope`` (a Component, or None across Components) inserts, and how
    many of them press, from the tree alone. A Component counts every
    instance, as a Component that builds its instances apart is checked."""

    copies_of = (lambda step: plan.totals[step]) if scope is None else (
        lambda step: plan.totals[step] // int(plan.geometries[scope]["count"]))
    instances = 1 if scope is None else int(plan.geometries[scope]["count"])
    insertions = presses = 0
    for item in plan.steps_in(scope):
        if item.get("joint") not in SWEPT:
            continue
        copies = copies_of(item["id"]) * (instances if scope is not None else 1)
        for entry in plan.inputs[item["id"]][1:]:
            many = copies * int(entry.get("count", 1))
            insertions += many
            if entry.get("press_mm"):
                presses += many
    return {"insertions": insertions, "presses": presses}


def tree_seconds(load: dict) -> float:
    """The time one tree check of ``load`` (``tree_load``) is allowed."""

    return TREE_MIN_S + TREE_INSERTION_S * load["insertions"] + TREE_PRESS_S * load["presses"]


def check_component(plan: Plan, geometry, role: str, nozzle: float) -> dict:
    """Everything one Component's round checks: its bodies against its
    leaves, their colours, and every step and route wholly inside it."""

    report = {"scope": "component:%s" % role, "defects": [], "slips": [], "failures": [], "conditions": [],
              "routes": [], "snaps": [], "presses": [], "seats": [],
              "holds": [], "wall_orders": []}
    seen = len(getattr(geometry, "fallbacks", ()))
    expected = plan.expected_labels(role)
    instances = geometry.instances(role)
    for instance in instances:
        bodies = geometry.component(role, instance)
        slips = reconcile(expected, bodies, plan, role)
        for slip in slips:
            if len(instances) > 1:
                slip["instance"] = instance
        report["slips"] += slips
        report["failures"] += [slip_failure(slip) for slip in slips]
        report["failures"] += colour_failures(plan, bodies)
        if slips:
            continue
        checked = _check(role, plan, geometry, keyed(plan, role, bodies), nozzle)
        for key in ("conditions", "failures", "routes", "snaps", "presses", "seats", "holds", "wall_orders"):
            report[key] += checked[key]
    report["failures"] = list(dict.fromkeys(report["failures"]))
    report["fallbacks"] = list(getattr(geometry, "fallbacks", ())[seen:])
    return report


def check_assembly(plan: Plan, geometry, nozzle: float, *, reconcile_all: bool = False) -> dict:
    """The checks across Components: every placed instance, then every step
    and route that spans Components. ``reconcile_all`` (final verification)
    also reconciles and colour-checks every Component."""

    report = {"scope": "final" if reconcile_all else "assembly", "defects": structure_defects(plan),
              "slips": [], "failures": [], "conditions": [], "routes": [], "snaps": [], "presses": [], "seats": [],
              "holds": [], "wall_orders": []}
    seen = len(getattr(geometry, "fallbacks", ()))
    bodies: dict[str, Body] = {}
    for role in sorted(plan.component_parts):
        expected = plan.expected_labels(role)
        for instance in range(1, int(plan.geometries[role]["count"]) + 1):
            built = geometry.component(role, instance)
            slips = reconcile(expected, built, plan, role)
            if reconcile_all:
                for slip in slips:
                    if plan.geometries[role]["count"] > 1:
                        slip["instance"] = instance
                report["slips"] += slips
                report["failures"] += [slip_failure(slip) for slip in slips]
                report["failures"] += colour_failures(plan, built)
            elif slips and not any(item["part"] == role for item in report["slips"]):
                slip = _defect("unreconciled", role, "part_%s does not match its leaves; its component round "
                               "names how" % role, component=role)
                report["slips"].append(slip)
                report["failures"].append(slip_failure(slip))
            bodies.update(keyed(plan, role, built, instance))
    if not report["defects"] and not report["slips"]:
        checked = _check(None, plan, geometry, bodies, nozzle)
        for key in ("conditions", "failures", "routes", "snaps", "presses", "seats", "holds", "wall_orders"):
            report[key] += checked[key]
        _holds(plan, geometry, bodies, report)
    report["failures"] = list(dict.fromkeys(report["failures"]))
    report["fallbacks"] = list(getattr(geometry, "fallbacks", ())[seen:])
    return report


def _isolated_offset(shape, depth: float, kind):
    """``shape`` offset inward by ``depth`` in a forked child (#392). The
    kernel's intersection join crashes the process on some solids (Kyoto
    S13's obstacles) and never finishes on others (Kyoto S61's); in a
    child that crash, or a join still running after PRESS_OFFSET_SECONDS,
    is a refused offset, and the caller takes the stricter arc join,
    instead of ending or stalling the round."""

    import os
    import signal
    import tempfile

    from build123d import export_brep, import_brep, offset

    handle, path = tempfile.mkstemp(suffix=".brep")
    os.close(handle)
    try:
        child = os.fork()
        if child == 0:  # pragma: no cover - runs in the child, which reports only by its exit status
            import faulthandler

            faulthandler.disable()  # a crash here is reported by the status alone
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.alarm(PRESS_OFFSET_SECONDS)  # a join the kernel never finishes is refused too
            code = 1
            try:
                code = 0 if export_brep(offset(shape, amount=-depth, kind=kind), path) is not False else 1
            except BaseException:  # noqa: BLE001 - any failure is a refusal
                code = 1
            os._exit(code)
        _pid, status = os.waitpid(child, 0)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            raise RuntimeError("the kernel's offset failed (child status %d)" % status)
        return import_brep(path)
    finally:
        os.unlink(path)


def _offset_key(base, depth: float, sharp: bool):
    """The key ``pressed`` keeps an unplaced shape's offset under, or None
    for a shape the kernel cannot write: that one is offset uncached."""

    try:
        return (_brep_digest(base), float(depth), bool(sharp))
    except Exception:  # noqa: BLE001 - a shape without bytes is offset uncached
        return None


def _brep_digest(shape) -> str:
    """The SHA-256 of a shape's exact BREP bytes: the key under which its
    offsets are kept."""

    import hashlib
    import io

    from build123d import export_brep

    stream = io.BytesIO()
    if export_brep(shape, stream) is False:
        raise RuntimeError("the kernel cannot write the shape")
    return hashlib.sha256(stream.getvalue()).hexdigest()


def _smaller(shape, whole):
    """``shape`` when it is one valid solid smaller than ``whole`` and
    inside it, else None. The kernel's offset can return a valid, smaller
    solid that fills a hole of ``whole`` (#392): its material outside
    ``whole`` would be checked as an obstacle it is not."""

    valid = shape.is_valid() if callable(shape.is_valid) else shape.is_valid
    if not (valid and 0 < shape.volume < whole.volume):
        return None
    try:
        outside = shape - whole
    except Exception:  # noqa: BLE001 - a shrink the kernel cannot compare is not taken
        return None
    if outside is not None and sum(part.volume for part in outside.solids()) > PRESS_INSIDE_MM3:
        return None
    return shape


class CadGeometry:
    """The build123d backend: builds each Component from its own source,
    placed by its assembly_pose, and sweeps with check_motion's conditions."""

    def __init__(self, project: Path, counts: dict | None = None) -> None:
        import runpy

        self.project = Path(project).resolve()
        self.counts = dict(counts or {})
        scripts = Path(__file__).resolve().parents[2] / "cad" / "scripts"
        self.motion = runpy.run_path(str(scripts / "check_motion"), run_name="kit_tree_check_motion")
        self.fallbacks: list[dict] = []
        self.press_eroded = 0
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
        group = self._group(moving)
        solids = list(group.solids())
        if len(solids) > 1:
            try:
                self.motion["rigid_material"](group)
            except ValueError as exc:
                return self._sweep_each(condition, solids, obstacles, exc)
        parts = {condition["inputs"]["moving_part"]: group}
        parts.update({body.key: body.shape for body in obstacles})
        swept = json.loads(json.dumps({key: value for key, value in condition.items() if key != "result"}))
        swept["inputs"]["obstacle_parts"] = [body.key for body in obstacles]
        result = self.motion["run_condition"](swept, parts, 0)
        if (len(solids) > 1 and result.get("status") not in ("pass", "fail")
                and condition["inputs"].get("press_offset") in ("local", "obstacles", "obstacles-local")):
            # A press offset's windows and rest, or a group against its
            # obstacles' (#392), the kernel cannot sweep as one: solid by
            # solid, never looser (``_sweep_each``).
            return self._sweep_each(condition, solids, obstacles, ValueError(result.get("detail")))
        return result

    def _sweep_each(self, condition: dict, solids: list, obstacles: list[Body], error: Exception) -> dict:
        """The moving group's union failed: sweep each solid on its own
        against every obstacle, each held to the overlap limit over the
        number of solids. A solid's overlap with an obstacle is at least its
        share of the union's, so the union passes whenever every solid does:
        never looser than the fused sweep. Recorded in ``fallbacks``."""

        base = json.loads(json.dumps({key: value for key, value in condition.items() if key != "result"}))
        base["inputs"]["obstacle_parts"] = [body.key for body in obstacles]
        limit = float(base["thresholds"]["maxOverlapMm3"]) / len(solids)
        name = base["inputs"]["moving_part"]
        outcome = None
        for index, solid in enumerate(solids, 1):
            one = json.loads(json.dumps(base))
            one["id"] = "%s.solid%d" % (base.get("id", name), index)
            one["thresholds"]["maxOverlapMm3"] = limit
            parts = {name: solid}
            parts.update({body.key: body.shape for body in obstacles})
            result = self.motion["run_condition"](one, parts, 0)
            if result.get("status") == "fail" or (result.get("status") != "pass" and outcome is None):
                outcome = result
            if result.get("status") == "fail":
                break
        self.fallbacks.append({"id": base.get("id"), "moving_part": name, "solids": len(solids),
                               "reason": str(error), "max_overlap_mm3_each": round(limit, 9),
                               "status": "pass" if outcome is None else outcome.get("status")})
        if outcome is None:
            return {"status": "pass", "detail": "clear solid by solid: %d solids each at most %.3g mm3, as their "
                                                "union failed (%s)" % (len(solids), limit, error)}
        return {**outcome, "detail": "%s (swept solid by solid, %d solids each at most %.3g mm3, as their union "
                                     "failed: %s)" % (outcome.get("detail"), len(solids), limit, error)}

    def snap_overlaps(self, condition: dict, moving: list[Body], obstacles: list[Body]) -> list[dict]:
        """Every solid where ``moving``, at each sample of the condition's
        translation from its seat (sample 0) outward, overlaps an obstacle:
        its sample, obstacle, volume and axis-aligned bounds. An axis-aligned
        box never reads a barb shallower than it is."""

        from build123d import Location, Vector

        inputs = condition["inputs"]
        steps, move = int(inputs["steps"]), Vector(*inputs["translation"])
        group = self._group(moving)
        found = []
        for step in range(0, steps + 1):
            moved = group.moved(Location(move * (step / steps)))
            box = moved.bounding_box()
            for body in obstacles:
                if _apart(box, _grown(body.shape.bounding_box(), 0.0)):
                    continue
                try:
                    common = moved.intersect(body.shape)
                except Exception as exc:                         # noqa: BLE001
                    raise RuntimeError("the overlap of %s and %s at step %d/%d could not be measured: %s"
                                       % (inputs["moving_part"], body.key, step, steps, exc)) from exc
                for solid in (common.solids() if common is not None else ()):
                    if solid.volume <= OVERLAP_MM3:
                        continue
                    bb = solid.bounding_box()
                    found.append({"step": step, "catch": body.key, "volume": float(solid.volume),
                                  "bounds": ((bb.min.X, bb.min.Y, bb.min.Z), (bb.max.X, bb.max.Y, bb.max.Z))})
        return found

    def pressed(self, moving: list[Body], depth: float, sharp: bool = False):
        """``moving`` offset inward by a press input's ``depth`` (ADR 0104
        amendment 2026-11-19): ``(bodies, None)``, or ``(None, reason)`` when
        the kernel cannot offset a body into one valid, smaller solid.
        ``sharp`` joins an obstacle's offset faces by intersection: an arc
        join rounds a socket's inner corners and puts material back where
        the input's corners sit. Where the kernel refuses that join, the arc
        join is taken: it leaves more material, so it is never looser."""

        from build123d import Kind, Location, offset

        found = []
        cache = self.__dict__.setdefault("_offsets", {})
        for body in moving:
            try:
                # The kernel refuses to offset some placed solids it offsets at
                # their own origin: offset the unplaced shape, then place it.
                place = body.shape.location
                base = body.shape.located(Location())
                # The same unplaced bytes shrink the same way (#394): an
                # obstacle shrunk again for a later input reuses the first
                # outcome, refusal included, instead of offsetting (or
                # stalling) again. Other bytes are offset anew.
                key = _offset_key(base, depth, sharp)
                outcome = cache.get(key) if key is not None else None
                if outcome is None:
                    outcome = self._offset(base, depth, sharp, Kind, offset)
                    if key is not None:
                        cache[key] = outcome
                shape, refusal = outcome
                if shape is None:
                    return None, refusal % body.key
                shape = shape.moved(place)
            except Exception as exc:  # noqa: BLE001 - an offset the kernel refuses is a refusal
                return None, "the kernel refuses to offset %s: %s" % (body.key, exc)
            found.append(Body(body.label, shape, key=body.key))
        return found, None

    @staticmethod
    def _offset(base, depth, sharp, Kind, offset):
        """``base`` offset inward by ``depth``: ``(shape, None)`` or ``(None,
        reason)`` whose ``%s`` takes the body's key."""

        try:
            shape = None
            if sharp:
                try:
                    shape = _smaller(_isolated_offset(base, depth, Kind.INTERSECTION), base)
                except Exception:  # noqa: BLE001 - the stricter arc join below decides
                    shape = None
            if shape is None:
                shape = _smaller(offset(base, amount=-depth, kind=Kind.ARC), base)
        except Exception as exc:  # noqa: BLE001 - an offset the kernel refuses is a refusal
            return None, "the kernel refuses to offset %%s: %s" % str(exc).replace("%", "%%")
        if shape is None:
            return None, "the offset of %s is no valid smaller solid"
        return shape, None

    def shrunk_obstacles(self, condition: dict, moving: list[Body], obstacles: list[Body], depth: float):
        """The other side of a press (ADR 0104 amendment 2026-11-27,
        #392): ``obstacles`` cropped to the box round every pose of the
        condition's sweep and offset inward by ``depth``, each whole where
        the kernel can and otherwise only in windows round where it
        overlaps the moving Part (``pressed_local`` with the motion
        reversed: the same relative poses). ``(bodies, "offset" | "local",
        None)`` or ``(None, None, reason)``; an obstacle that cannot be
        shrunk is a refusal.

        Each offset takes the sharp join, which moves each face back by
        ``depth`` and keeps a socket's inner corners square, as the
        obstacle offset always has: an oversize square peg bites a square
        socket's corners by sqrt 2 times its face bite. Where the kernel
        refuses that join, the stricter arc join or boolean shrink is
        taken."""

        from build123d import Location, Vector

        inputs = condition["inputs"]
        steps, move = int(inputs["steps"]), Vector(*inputs["translation"])
        group = self._group(moving)
        boxes = [group.moved(Location(move * (step / steps))).bounding_box() for step in range(steps + 1)]
        reverse = json.loads(json.dumps({key: value for key, value in condition.items() if key != "result"}))
        reverse["inputs"]["translation"] = [-c for c in inputs["translation"]]
        found, kind = [], "offset"
        for body in obstacles:
            try:
                local = self.motion["crop_to_sweep"](body.shape, boxes)
            except Exception:  # noqa: BLE001 - an obstacle the kernel cannot crop is offset whole
                local = body.shape
            if local is None:
                continue
            cropped = Body(body.label, local, key=body.key)
            shrunk, error = self.pressed([cropped], depth, sharp=True)
            if error is None:
                found.extend(shrunk)
                continue
            # The obstacle moves against the Part: the reversed motion gives
            # the same relative poses, so its windows lie round the overlaps.
            windows, why = self.pressed_local(json.loads(json.dumps(reverse)), [cropped], moving, depth,
                                              sharp=True)
            if windows is None:
                return None, None, "%s; nor in windows round its overlaps: %s" % (error, why)
            kind = "local"
            # Each piece keeps its own key (``@press<n>``, ``@rest``): the
            # sweep keys its parts by it, and one key would keep one piece.
            found.extend(windows)
        return found, kind, None

    def pressed_local(self, condition: dict, moving: list[Body], obstacles: list[Body], depth: float,
                      sharp: bool = False):
        """``moving`` offset inward by a press input's ``depth`` only where
        it can bite, for a Part (or, with the motion reversed, an obstacle)
        the kernel cannot offset whole (ADR 0104 amendment 2026-11-26, press
        local offset):
        ``(bodies, None)`` or ``(None, reason)``.

        At every pose of the condition's sweep the Part's overlap with each
        obstacle is measured; each overlap's box, in the Part's own frame,
        grown by a margin M > ``depth`` (and split into tiles no longer than
        PRESS_LOCAL_TILE_MM) is a window. The Part is cut to each window and
        each cut solid is offset inward by ``depth``. A point of an overlap
        lies at least M from its window's cut faces, so it is deeper than
        ``depth`` in the cut exactly when it is deeper than ``depth`` in the
        whole Part: the windows' offsets overlap the obstacles exactly where
        the whole Part's offset would, at the same sampled poses, and hold
        nothing the whole offset does not. Swept at the same overlap limit,
        the gate is the input offset's, unchanged. With no overlap at any
        pose the Part itself is returned, unshrunk. Any overlap the kernel
        cannot measure, cut or offset is a refusal, never a pass."""

        from build123d import Box, Location, Vector

        inputs = condition["inputs"]
        steps, move = int(inputs["steps"]), Vector(*inputs["translation"])
        group = self._group(moving)
        boxes = [group.moved(Location(move * (step / steps))).bounding_box() for step in range(steps + 1)]
        self.press_eroded = 0
        near = []
        for body in obstacles:
            try:
                local = self.motion["crop_to_sweep"](body.shape, boxes)
            except Exception:  # noqa: BLE001 - an obstacle the kernel cannot crop is measured whole
                local = body.shape
            if local is not None:
                near.append((body.key, local))
        found = []
        for step in range(steps + 1):
            shift = move * (step / steps)
            moved = group.moved(Location(shift))
            box = moved.bounding_box()
            for key, shape in near:
                if _apart(box, _grown(shape.bounding_box(), 0.0)):
                    continue
                try:
                    common = moved.intersect(shape)
                except Exception as exc:  # noqa: BLE001 - an unmeasured overlap is a refusal
                    return None, "the overlap with %s at step %d/%d cannot be measured: %s" % (key, step, steps, exc)
                for solid in (common.solids() if common is not None else ()):
                    if solid.volume <= 0:
                        continue
                    bb = solid.bounding_box()
                    found.append(((bb.min.X - shift.X, bb.min.Y - shift.Y, bb.min.Z - shift.Z),
                                  (bb.max.X - shift.X, bb.max.Y - shift.Y, bb.max.Z - shift.Z)))
        if not found:
            return moving, None
        windows = _press_windows(found)
        solids = list(group.solids())
        shrunk, why, used = [], None, []
        for index, (lo, hi) in enumerate(windows, 1):
            piece = None
            for margin in PRESS_LOCAL_MARGINS_MM:
                piece, why = self._press_window(solids, lo, hi, margin + depth, depth, Box, Location, sharp)
                if piece is not None:
                    used.append((lo, hi, margin + depth))
                    break
            if piece is None:
                return None, "its window %d of %d round its overlaps cannot be offset: %s" % (index, len(windows), why)
            shrunk += [Body(moving[0].label, shape, key="%s@press%d" % (moving[0].key, index)) for shape in piece]
        # The rest of the Part, outside every window, sweeps as it is: it
        # overlaps nothing, and were an overlap missed it would still fail.
        try:
            rest = group
            for lo, hi, margin in used:
                low = [v - margin for v in lo]
                high = [v + margin for v in hi]
                rest = rest - (Location(tuple((a + b) / 2 for a, b in zip(low, high)))
                               * Box(*(b - a for a, b in zip(low, high))))
        except Exception as exc:  # noqa: BLE001 - a Part the kernel cannot cut is a refusal
            return None, "the kernel cannot cut the windows from the rest of the Part: %s" % exc
        shrunk += [Body(moving[0].label, part, key="%s@rest" % moving[0].key)
                   for part in (rest.solids() if rest is not None else ()) if part.volume > 0]
        condition["inputs"]["press_windows"] = len(windows)
        if self.press_eroded:
            condition["inputs"]["press_eroded"] = self.press_eroded
        return shrunk, None

    def _press_window(self, solids, lo, hi, margin, depth, Box, Location, sharp=False):
        """Each solid of the Part cut to the box ``lo``-``hi`` grown by
        ``margin``, offset inward by ``depth``: ``(shapes, None)`` or
        ``(None, reason)``."""

        low = [v - margin for v in lo]
        high = [v + margin for v in hi]
        window = Location(tuple((a + b) / 2 for a, b in zip(low, high))) * Box(*(b - a for a, b in zip(low, high)))
        shapes = []
        for solid in solids:
            if _apart(solid.bounding_box(), (tuple(low), tuple(high))):
                continue
            try:
                cut = solid & window
            except Exception as exc:  # noqa: BLE001 - a window the kernel cannot cut is a refusal
                return None, "the kernel cannot cut the Part to it: %s" % exc
            for part in (cut.solids() if cut is not None else ()):
                if part.volume <= 0:
                    continue
                pressed, error = self.pressed([Body(None, part, key="window")], depth, sharp=sharp)
                if error is None:
                    shapes.append(pressed[0].shape)
                    continue
                eroded, why = self.eroded(part, depth)
                if eroded is None:
                    return None, "%s; nor by booleans: %s" % (error, why)
                self.press_eroded += 1
                shapes.extend(eroded)
        return shapes, None

    def eroded(self, shape, depth: float):
        """``shape`` shrunk by booleans alone, for a window cut the kernel
        cannot offset (ADR 0104 amendment 2026-11-26, press local offset):
        the common of ``shape`` with copies of itself moved ``depth`` along
        each of its face normals, both ways (three by three points of each
        curved face, one per PRESS_ERODE_CURVED cone), and along the
        bisector of the two flat faces at each edge: ``(solids, None)`` or
        ``(None, reason)``.

        A point is kept only if every point ``depth`` from it along those
        directions is in ``shape``; the arc offset keeps it only if every
        point within ``depth`` is. So this keeps all the arc offset keeps,
        and more only beside concave edges and curved faces: it is never
        looser, and it is the same on a flat face. Unlike the offset it
        takes a face the press removes whole. A boolean the kernel reports
        as failed, or a result missing a sampled point deeper than
        ``depth`` in ``shape``, is a refusal."""

        from build123d import GeomType, Location, Solid, Vector
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS

        directions = []
        try:
            faces = sorted(shape.faces(), key=lambda face: face.geom_type != GeomType.PLANE)
            for face in faces:
                flat = face.geom_type == GeomType.PLANE
                samples = ((0.5, 0.5),) if flat else tuple(
                    (u, v) for u in (0.1, 0.5, 0.9) for v in (0.1, 0.5, 0.9))
                for u, v in samples:
                    normal = face.normal_at(u, v)
                    if normal.length <= 0:
                        continue
                    for sign in (1.0, -1.0):
                        direction = (normal * sign).normalized()
                        near = PRESS_ERODE_SAME if flat else PRESS_ERODE_CURVED
                        if all(direction.dot(other) < near for other in directions):
                            directions.append(direction)
            # Across each edge between two flat faces, the bisector of their
            # normals both ways: without it the shrink keeps a depth-square
            # of material along a socket's inner corner, where the arc offset
            # keeps none.
            for first, second in _flat_face_pairs(shape, GeomType):
                for sign in (1.0, -1.0):
                    middle = first + second
                    if middle.length <= 1e-6:
                        continue
                    direction = (middle * sign).normalized()
                    if all(direction.dot(other) < PRESS_ERODE_SAME for other in directions):
                        directions.append(direction)
            kept = shape.wrapped
            for direction in directions:
                moved = shape.moved(Location(direction * depth)).wrapped
                common = BRepAlgoAPI_Common(kept, moved)
                if not common.IsDone():
                    return None, "the kernel's boolean fails"
                kept = common.Shape()
            # Merge the faces the chain split, as build123d's own booleans
            # do: the same geometry, which later booleans handle better.
            unify = ShapeUpgrade_UnifySameDomain(kept, True, True, True)
            unify.AllowInternalEdges(False)
            unify.Build()
            kept = unify.Shape()
            solids = []
            explorer = TopExp_Explorer(kept, TopAbs_SOLID)
            while explorer.More():
                solid = Solid(TopoDS.Solid_s(explorer.Current()))
                if solid.volume > 0:
                    if not solid.is_valid or solid.volume > shape.volume:
                        return None, "the kernel's boolean gives no valid smaller solid"
                    solids.append(solid)
                explorer.Next()
        except Exception as exc:  # noqa: BLE001 - a shrink the kernel cannot make is a refusal
            return None, "the kernel's boolean fails: %s" % exc
        missing = _deep_point_missing(shape, solids, depth)
        if missing is not None:
            return None, "its shrink drops a point %.3f mm deep at %s" % missing
        return solids, None

    def touching(self, a, b, gap: float) -> bool:
        """Whether two placed shapes come within ``gap`` of each other."""

        try:
            return a.distance_to(b) <= gap
        except Exception:  # noqa: BLE001 - an unmeasurable pair is not judged touching
            return False

    def _overlap(self, a, b) -> float:
        try:
            return float(self.motion["overlap_volume"](a, b))
        except Exception:  # noqa: BLE001 - an unmeasured overlap is no hold
            return 0.0

    def _box(self, shape):
        """A shape's bounding box, computed once per shape for the run."""

        cache = self.__dict__.setdefault("_boxes", {})
        found = cache.get(id(shape))
        if found is None or found[0] is not shape:
            found = cache[id(shape)] = (shape, shape.bounding_box())
        return found[1]

    def hold(self, unit: list, host: list, floor: float | None = None) -> dict:
        """The tilt hold quantities of one unit against its host (ADR 0104
        amendment 2026-11-19, rule i), in the assembly frame, +Z up.
        ``floor`` is the toy's lowest level, the table it stands on.

        - ``z_bear``: the bearing level, the highest of the unit's downward
          flat faces (normal Z at most BEARING_NZ) within BEARING_GAP_MM of
          the host or of the floor; the footprint is their plan bounds.
          With none, the unit's lowest level and no footprint: it tips at 0.
        - ``H``: the unit's height above the bearing level; ``d`` how far it
          reaches below it (pegs, spigots, tabs).
        - ``tip``: per way, the tilt at which its centre of mass passes the
          footprint's edge on that side.
        - ``lift``: whether a HOLD_PUSH_MM lift meets the host by more than
          HOLD_HIT_MM3 beyond its seat's own overlap (a snap or detent holds
          it down).
        - ``slide``: per way, whether a HOLD_PUSH_MM push that way does.
        - ``catch``: per way, the least of HOLD_CATCH_SAMPLES_DEG turned
          rigidly about that footprint edge, the far side lifting, at which
          it does; None when it does not by HOLD_CATCH_DEG.

        Only what the verdict needs is measured; the rest is None. A way
        that tips at HOLD_TILT_DEG or more needs nothing; when every way
        does, nothing moves. Otherwise the lift is measured; a held lift
        needs nothing more. A way that tips sooner has its slide measured,
        and its catch only when the slide is held: first at HOLD_CATCH_DEG,
        then down the samples. At most 1 + 1 + 4 x (1 + 3) measures per
        unit, each moving only the unit bodies within reach of the host
        against the host material within reach of them."""

        from build123d import Axis, Compound, Location, Solid, Vector

        boxes = [self._box(shape) for shape in unit]
        lo = Vector(min(b.min.X for b in boxes), min(b.min.Y for b in boxes), min(b.min.Z for b in boxes))
        hi = Vector(max(b.max.X for b in boxes), max(b.max.Y for b in boxes), max(b.max.Z for b in boxes))
        reach = max(1.0, (hi - lo).length * math.radians(HOLD_CATCH_DEG) + HOLD_PUSH_MM)
        levels, plan_points = [], []
        for index, shape in enumerate(unit):
            for face in shape.faces():
                try:
                    if face.geom_type.name != "PLANE" or face.area < 0.5:
                        continue
                    if face.normal_at().Z > BEARING_NZ:
                        continue
                    box = face.bounding_box()
                    on_floor = floor is not None and abs(box.min.Z - floor) <= BEARING_GAP_MM
                    if not on_floor:
                        grown = _grown(box, BEARING_GAP_MM)
                        close = [other for other in host if not _apart(self._box(other), grown)]
                        if not any(face.distance_to(other) <= BEARING_GAP_MM for other in close):
                            continue
                except Exception:  # noqa: BLE001 - an unreadable face bears nothing
                    continue
                levels.append(box.min.Z)
                plan_points += [(box.min.X, box.min.Y), (box.max.X, box.max.Y)]
        bearing = bool(levels)
        z = max(levels) if bearing else lo.Z
        if bearing:
            x0, x1 = min(p[0] for p in plan_points), max(p[0] for p in plan_points)
            y0, y1 = min(p[1] for p in plan_points), max(p[1] for p in plan_points)
        else:
            x0, x1, y0, y1 = lo.X, hi.X, lo.Y, hi.Y
        volumes = [max(shape.volume, 1e-9) for shape in unit]
        centres = [shape.center() for shape in unit]
        mass = sum(volumes)
        com = sum((c * v for c, v in zip(centres, volumes)), Vector(0, 0, 0)) * (1.0 / mass)
        rise = max(com.Z - z, 1e-6)
        edges = {"+X": (x1, com.X, 1), "-X": (x0, com.X, -1), "+Y": (y1, com.Y, 1), "-Y": (y0, com.Y, -1)}
        record = {"z_bear": round(z, 3), "bearing": bearing, "H": round(hi.Z - z, 3), "d": round(z - lo.Z, 3),
                  "tip": {}, "lift": None, "slide": dict.fromkeys(WAYS), "catch": dict.fromkeys(WAYS)}
        for way in WAYS:
            edge, centre, sign = edges[way]
            reachable = (edge - centre) * sign if bearing else 0.0
            record["tip"][way] = round(math.degrees(math.atan2(max(reachable, 0.0), rise)), 2)
        weak = [way for way in WAYS if record["tip"][way] < HOLD_TILT_DEG]
        if not weak:
            return record

        # Each unit body with the host material within reach of it: no
        # sampled move takes a body farther, so each host body is clipped
        # once to the body's box grown by that reach, and every measure runs
        # against those small pieces. A host body the kernel cannot clip is
        # measured whole.
        pairs = []
        for index, shape in enumerate(unit):
            grown = _grown(boxes[index], reach)
            region = Solid.make_box(*(grown[1][a] - grown[0][a] for a in range(3))).moved(Location(grown[0]))
            close = []
            for other in host:
                if _apart(self._box(other), grown):
                    continue
                try:
                    piece = other.intersect(region)
                    parts = [] if piece is None else (
                        [solid for item in piece for solid in item.solids()] if isinstance(piece, list)
                        else list(piece.solids()))
                    if not parts:
                        continue
                    piece = parts[0] if len(parts) == 1 else Compound(parts)
                    close.append((piece, _grown(piece.bounding_box(), 0.0)))
                except Exception:  # noqa: BLE001 - an unclipped body is measured whole
                    close.append((other, _grown(self._box(other), 0.0)))
            if close:
                pairs.append((shape, close))

        def total(move, limit=None):
            found = 0.0
            for shape, close in pairs:
                moved = move(shape)
                box = moved.bounding_box()
                for other, bounds in close:
                    if _apart(box, bounds):
                        continue
                    found += self._overlap(moved, other)
                    if limit is not None and found > limit:
                        return found
            return found

        limit = total(lambda shape: shape) + HOLD_HIT_MM3

        def meets(move):
            return total(move, limit) > limit

        record["lift"] = meets(lambda shape: shape.moved(Location((0, 0, HOLD_PUSH_MM))))
        if record["lift"]:
            return record
        pushes = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0)}
        for way in weak:
            shift = tuple(HOLD_PUSH_MM * c for c in pushes[way])
            record["slide"][way] = meets(lambda shape: shape.moved(Location(shift)))
            if not record["slide"][way]:
                continue
            edge, _, sign = edges[way]
            if way.endswith("X"):
                axis, turn = Axis((edge, 0, z), (0, 1, 0)), sign
            else:
                axis, turn = Axis((0, edge, z), (1, 0, 0)), -sign

            def turned(angle):
                return meets(lambda shape: shape.rotate(axis, turn * angle))

            if not turned(HOLD_CATCH_DEG):
                continue
            record["catch"][way] = next(angle for angle in HOLD_CATCH_SAMPLES_DEG
                                        if angle == HOLD_CATCH_DEG or turned(angle))
        return record

    def nonparallel(self, moving, obstacles, direction, exempt=(), seats=None) -> list[str]:
        """Every mating face pair at the seat that does not slide along
        ``direction``. A pair is a face of the input and a face of what it
        joins, of one kind and parallel to each other, within JOINT_GAP_MM:
        two flat faces (tab and slot walls, a seat and its stop) or two
        cylinders or cones on parallel axes (a peg and its bore, a pin and
        its lug). Flat pairs must face along or across the direction; round
        pairs must have their axis along it. A chamfer, a fillet or a body
        merely passing near another is no pair, so it is never judged.
        ``exempt`` lists declared snap pairs (``_ramps``): a flat face of a
        pair's snapping Part wholly inside its region, mating a face of that
        pair's catch, is the barb's ramp; it is appended to the entry's
        ``faces`` instead of being found, and the face's other pairs are
        still judged. ``seats``, given only when the input's sweep is clean,
        collects every flagged face of the input that is a seat face (ADR 0104
        amendment 2026-11-19): its outward normal leads into the stop, n.d > 0
        at every sample point, so it parts from its mate as the input backs
        out. A seat face is not found. Two faces are a pair only when they face
        each other across the gap (``_faces_each_other``, rule h): faces of
        neighbouring Parts facing the same way, one flush surface across a
        seam, or meeting only along an edge, are no pair."""

        from build123d import GeomType, Vector

        unit = Vector(*direction)
        limit = math.radians(PARALLEL_TOLERANCE_DEG)
        found = []
        targets = []
        for obstacle in obstacles:
            for face in obstacle.faces():
                read = _face_frame(face, GeomType)
                if read is not None:
                    targets.append((face, read, _grown(face.bounding_box(), JOINT_GAP_MM), obstacle))
        for shape in moving:
            for face in shape.faces():
                read = _face_frame(face, GeomType)
                if read is None:
                    continue
                kind, vector = read
                box = face.bounding_box()
                for other, (other_kind, other_vector), grown, owner in targets:
                    if other_kind != kind or _apart(box, grown):
                        continue
                    if abs(_dot(vector, other_vector)) < math.cos(limit):
                        continue
                    try:
                        if face.distance_to(other) > JOINT_GAP_MM:
                            continue
                    except Exception:  # noqa: BLE001 - an unmeasurable pair is not judged
                        continue
                    if not _faces_each_other(face, other):
                        continue   # rule h: a flush surface across a seam, or an edge, is no joint
                    angle = math.acos(min(1.0, abs(_dot(vector, (unit.X, unit.Y, unit.Z)))))
                    if kind == "plane" and limit < angle < math.pi / 2 - limit:
                        message = "a flat joint face at %.0f deg to it near %s" % (
                            math.degrees(angle), _point(face.center()))
                        ramp = _ramp_of(exempt, shape, owner, box)
                        if ramp is not None:
                            ramp["faces"].append(message)
                            continue
                    elif kind == "round" and angle > limit:
                        message = "a peg, bore or pin whose axis is %.0f deg off it near %s" % (
                            math.degrees(angle), _point(face.center()))
                    else:
                        break
                    if seats is not None and _seat_face(face, unit):
                        seats.append(message)
                    else:
                        found.append(message)
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


def _flat_face_pairs(shape, GeomType) -> list:
    """The outward normals of each two flat faces of ``shape`` that share an
    edge and are not parallel, once per pair."""

    faces = [face for face in shape.faces() if face.geom_type == GeomType.PLANE]
    edges = [{edge.wrapped.__hash__() for edge in face.edges()} for face in faces]
    found = []
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            if not edges[i] & edges[j]:
                continue
            a, b = faces[i].normal_at(), faces[j].normal_at()
            if abs(a.normalized().dot(b.normalized())) < 1.0 - 1e-9:
                found.append((a.normalized(), b.normalized()))
    return found


def _deep_point_missing(shape, solids, depth: float, per_axis: int = PRESS_ERODE_SAMPLES):
    """The first point of a grid over ``shape``'s box lying deeper than
    ``depth`` (plus 1e-3) inside ``shape`` but in none of ``solids``, as
    ``(depth, point)``, or None. Every such point belongs in any inward
    shrink by ``depth``: a guard against a boolean that silently drops
    material, which would loosen the gate."""

    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN

    box = shape.bounding_box()
    lo, hi = (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z)
    skin = shape.shells()
    for i in range(per_axis):
        for j in range(per_axis):
            for k in range(per_axis):
                point = gp_Pnt(*(a + (b - a) * (n + 0.5) / per_axis for a, b, n in zip(lo, hi, (i, j, k))))
                if BRepClass3d_SolidClassifier(shape.wrapped, point, 1e-7).State() != TopAbs_IN:
                    continue
                vertex = BRepBuilderAPI_MakeVertex(point).Vertex()
                deep = min(BRepExtrema_DistShapeShape(vertex, shell.wrapped).Value() for shell in skin)
                if deep <= depth + 1e-3:
                    continue
                if not any(BRepClass3d_SolidClassifier(solid.wrapped, point, 1e-7).State() == TopAbs_IN
                           for solid in solids):
                    return deep, "(%.3f, %.3f, %.3f)" % (point.X(), point.Y(), point.Z())
    return None


def _press_windows(boxes, tile: float = PRESS_LOCAL_TILE_MM) -> list:
    """The overlap boxes of a press sweep, ``(lo, hi)`` in the Part's frame,
    as windows: a box inside another drops, and a box longer than ``tile`` on
    a side is split into tiles no longer than it, which together cover it."""

    kept = []
    for lo, hi in sorted(boxes, key=lambda b: -math.prod(max(h - l, 1e-9) for l, h in zip(*b))):
        if any(all(a <= l and h <= b for l, h, a, b in zip(lo, hi, klo, khi)) for klo, khi in kept):
            continue
        kept.append((tuple(lo), tuple(hi)))
    windows = []
    for lo, hi in kept:
        counts = [max(1, math.ceil((h - l) / tile - 1e-9)) for l, h in zip(lo, hi)]
        spans = [(h - l) / n for l, h, n in zip(lo, hi, counts)]
        for i in range(counts[0]):
            for j in range(counts[1]):
                for k in range(counts[2]):
                    index = (i, j, k)
                    windows.append((tuple(l + s * n for l, s, n in zip(lo, spans, index)),
                                    tuple(l + s * (n + 1) for l, s, n in zip(lo, spans, index))))
    return windows


def _grown(box, margin):
    return ((box.min.X - margin, box.min.Y - margin, box.min.Z - margin),
            (box.max.X + margin, box.max.Y + margin, box.max.Z + margin))


def _grown_vectors(lo, hi, margin):
    return ((lo.X - margin, lo.Y - margin, lo.Z - margin), (hi.X + margin, hi.Y + margin, hi.Z + margin))


def _apart(box, grown) -> bool:
    lo, hi = grown
    return (box.min.X > hi[0] or box.max.X < lo[0] or box.min.Y > hi[1] or box.max.Y < lo[1]
            or box.min.Z > hi[2] or box.max.Z < lo[2])


# ---------------------------------------------------------------------------
# reports, the pilot's defect ledger, and the command line


def summarise(report: dict) -> dict:
    report.setdefault("slips", [])
    report["verdict"] = "DEFECT" if report["defects"] else "FAIL" if report["failures"] else "PASS"
    return report


def defect_need(report: dict) -> str:
    """The need a contract tree defect stops the run with (ADR 0092
    decision 10). A labelling slip never reaches here (Q28)."""

    shown = "; ".join("%s %s: %s" % (item["kind"], item["part"], item["detail"]) for item in report["defects"][:6])
    return ("Tree defect, reported to the owner, never repaired in the run (ADR 0092 decision 10): %s. "
            "Log it in the toy's TREE-ISSUES.md and correct the Design Contract's Assembly Tree." % shown)


def not_printed(plan: Plan) -> list[dict]:
    """Every Bought Part body of the whole toy, never printed (Q29): one entry
    per occurrence, ``<id>#n`` numbered across the toy as the gates key it,
    with its Component and catalogue id. It reads the tree, not geometry, so
    it is deterministic; reconciliation proves the bodies match it."""

    entries = (plan.catalogue.get("bought_parts") or {})
    found = []
    for part in sorted(plan.bought):
        catalogue_id = plan.parts[part]["bought"]
        for n in range(1, plan.totals.get(part, 0) + 1):
            found.append({"body": "%s#%d" % (part, n), "part": part, "bought": catalogue_id,
                          "name": str((entries.get(catalogue_id) or {}).get("name", "")),
                          "component": plan.component_of.get(part)})
    return found


def not_printed_document(kit: dict) -> dict:
    """``measure/not-printed.json``: the list final verification writes."""

    return {"kind": NOT_PRINTED_KIND, "schema_version": 1, "tree_sha256": tree_digest(kit),
            "colour": BOUGHT_PART_HEX,
            "note": "Bought Parts: bought, never printed. Each is modelled in the STEP for fit only and "
                    "coloured %s; do not print these bodies." % BOUGHT_PART_HEX,
            "bodies": not_printed(Plan(kit))}


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
        lines.append("TREE DEFECT: stop. The sealed contract's tree does not hold together; do not change the "
                     "model to hide it; the Workshop Manager stops the run with this need: %s"
                     % defect_need(report))
    elif report.get("slips"):
        lines.append("LABELLING SLIP: the built bodies do not match the tree; repair them in the next round "
                     "like any failing gate (Q28). The run continues.")
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
        report["not_printed"] = not_printed(plan)
    return summarise(report)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", nargs="?", help="the CAD project")
    parser.add_argument("--install", metavar="CAD_PROJECT", help="install the sealed Assembly Tree")
    parser.add_argument("--wish", help="with --install: the run's WISH.json")
    parser.add_argument("--contract", help="with --install outside a run: the Design Contract file "
                                           "(the Contract Proof, ADR 0096)")
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
            if bool(args.wish) == bool(args.contract):
                parser.error("--install needs exactly one of --wish <run>/WISH.json or --contract CONTRACT.md")
            result = (install(Path(args.install), Path(args.wish)) if args.wish
                      else install_contract(Path(args.install), Path(args.contract)))
            print(json.dumps(result, sort_keys=True))
            return EXIT_PASS
        if not args.project or not (args.component or args.assembly or args.final):
            parser.error("give a CAD project and one of --component, --assembly or --final")
        project = Path(args.project)
        selected = "component" if args.component else "final" if args.final else "assembly"
        report = run(project, selected, args.component.removeprefix("part_").removesuffix(".step.py")
                     if args.component else None, args.nozzle)
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
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
        (project / "measure" / NOT_PRINTED_FILE).write_text(
            json.dumps(not_printed_document(read_install(project)), indent=1, sort_keys=True) + "\n",
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
    try:  # timed in the Workshop timing ledger (ADR 0106); it only records
        from workshop.runtime.timing_ledger import script_main
    except Exception:  # noqa: BLE001 - a bare run copy has no ledger
        script_main = None
    sys.exit(main() if script_main is None else script_main('kit_tree', main, modes=("--self-check", "--install", "--component", "--assembly", "--final"), default_mode="install"))
