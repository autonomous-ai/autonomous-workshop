#!/usr/bin/env python3
"""Put a powered toy's Bought Parts into its model, and draw its circuit
(ADR 0095 amendment of 2026-11-01).

    bought_model.py <cad-project> --build [--json]
    bought_model.py <cad-project> --final [--json]

A schema 10 Design Contract states its circuit (``electrical``), and Make's
power report (``measure/power.json``) seats every carried part in a mount
envelope that ``check_mount`` judged (``cad.source``, a validation STEP in
the assembly frame). Without this tool the sealed model holds only the
printed parts: the toy looks like an empty shell and nothing shows where the
receptacle, switches, LEDs and resistors go.

``--build`` draws one body per Bought Part instance from the sealed
catalogue snapshot's ``model`` (its form, built from the entry's own sizes,
or the owner's redistributable vendor STEP) and seats it in that part's
envelope, oriented by the Make-authored placements file
``measure/bought-placements.json``::

    {"kind": "bought-placements", "schema_version": 1,
     "parts": {"usb-c": {"facing": "+y"}, "s-half": {"facing": "+z", "hinge": "+x"}},
     "routes": [{"wire": "wire", "from": "s-half", "to": "pcba",
                 "points": [[2.4, 16.6, 13.6], [2.4, 29.0, 13.6], [2.4, 29.0, 9.0]]}]}

``facing`` is the side a part works through: a receptacle's mouth, an LED's
light, a lever switch's lever. ``hinge`` is the end a lever is hinged at.
An optional ``pose`` seats a part whose mount is not square to the world
axes, such as a switch square to a tilted deck::

    "sw": {"facing": "+z", "pose": {"axis": [1, 0, 0], "angle_deg": 30}}

It is the right-handed rotation, about the centre of the envelope's world
bounding box, that turns the world axes into the part's own. The envelope is
read in that rotated frame and the body is planned there exactly as an
unrotated one (``facing`` and ``hinge`` name the part's own axes), then
turned into place. In the body list a posed body's ``seat`` and ``bounds``
are in the part's frame, beside its ``pose`` and that ``centre``; a route
end is measured to it in that frame. A part with no ``pose`` is drawn
exactly as before.
A ``box`` whose catalogue entry states both a ``body`` and a ``plunger``
size, a push switch, is drawn as the ``body`` with the plunger as a nose of
the plunger's cross-section centred on its ``facing`` side, which it needs:
the nose is as long as the ``body with plunger out`` height above the body's,
or the plunger's own length. Every other ``box`` is one block.
A body seats against its envelope's face opposite ``facing``, centred across
it; a body larger than its envelope on any axis fails, because the catalogue
part would not fit the mount Make sealed. The factory-assembled board, when
the contract names a ``pcba``, is drawn exactly at the contract's
``pcba.bounds_mm``: the board is no catalogue part, so only the contract may
state its outline, and nothing here estimates it. A route is a wire's polyline, swept at the wire's lead diameter; each
end lies within ``ROUTE_REACH_MM`` of the body it joins. Routes are optional:
a circuit drawn with none still has its wiring diagram.

It writes ``bought/<name>.step`` per body and ``bought/__init__.py``, whose
``bought_group()`` the assembly entry adds to its compound, so the regenerated
assembly STEP carries a ``bought`` group of leaves named ``bought_<part>``
in the reserved not-printed magenta (ADR 0092, Q29). None of them is a
``part_*`` entry, so no print gate ever reads one, and no occurrence of the
group has a ``parts/`` production STEP. It also writes
``measure/bought-bodies.json``, the list of bodies with their forms, sources
and licences, bound to every input's hash.

``--final`` (run by final verification) replans from the same inputs and
refuses a body list, STEP file or bound that changed, then writes the
electrical pictures and text into ``measure/electrical/``:

- ``exploded.png``: the bought bodies backed out along their facing, labelled;
- ``cutaway.png``: the assembled toy with the printed parts cut away on the
  camera's side, every bought body in place and labelled;
- ``wiring.png``: the diagram of the contract's paths: each part, each
  connection along a path, and how it is joined (a board trace on the PCBA,
  otherwise the contract's ``joins`` by its ``assembled_by``);
- ``assembly.md``: the Electrical Assembly text, written from the contract's
  ``electrical`` fields and the sealed catalogue names alone, which the
  product README carries verbatim;
- ``electrical.json``: what was drawn and every file's hash, which the host
  checks before Make is accepted.

Nothing here judges anything: every picture and sentence follows from the
sealed contract, the catalogue snapshot, the power report's envelopes and the
placements file. Exit status: 0 written, 1 refused (every reason printed),
2 bad usage.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
RENDER_REVIEW_SCRIPT = SCRIPTS.parents[1] / "cad" / "scripts" / "render_review"

BODIES_PATH = "measure/bought-bodies.json"
PLACEMENTS_PATH = "measure/bought-placements.json"
POWER_PATH = "measure/power.json"
ELECTRICAL_DIR = "measure/electrical"
BOUGHT_DIR = "bought"
BODIES_KIND = "bought-bodies"
PLACEMENTS_KIND = "bought-placements"
ELECTRICAL_KIND = "electrical-pictures"
SCHEMA_VERSION = 1
ELECTRICAL_SCHEMA_VERSION = 10
# The occurrence-name prefix of every bought body, which the host exempts
# from the production-part and filament-name rules and checks against this
# tool's list instead.
OCCURRENCE_PREFIX = "bought_"
GROUP_LABEL = "bought"
BOARD_ID = "pcba"
# ADR 0092 decision 5 (Q29): every Bought Part body in every STEP carries it.
# The catalogue validator and kit_tree.py hold the same value; a test keeps
# them one.
BOUGHT_PART_HEX = "#ff00ff"
FIT_TOLERANCE_MM = 0.05
BOUND_TOLERANCE_MM = 0.02
ROUTE_REACH_MM = 1.0
MAX_ROUTES = 32
MAX_ROUTE_POINTS = 32
POSE_KEYS = {"axis", "angle_deg"}
# Forms whose working side must be stated: guessing it would draw a socket
# facing into the toy or an LED shining at its board.
DIRECTIONAL = ("receptacle", "lever-switch", "radial-led", "smd-led")
# The forms of the catalogue (wish/catalogues.py MODEL_FORMS) plus the two
# this tool adds: a part with no model is its envelope, the board is its own.
FORMS = ("box", "receptacle", "lever-switch", "radial-led", "smd-led", "chip", "axial",
         "cylinder", "plate", "wire", "envelope", "board")
DEFAULT_LEAD_MM = 0.6
LEVER_RISE_MM = 2.0
LEVER_TIP_INSET_MM = 1.0
LEVER_THICKNESS_MM = 0.3
LED_FLANGE_MM = 1.0
LED_FLANGE_STEP_MM = 0.9
AXES = {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1), "+z": (2, 1), "-z": (2, -1)}

# Front-right and above, in the contract frame where -Y is the front: the
# side a buyer faces, so the cut removes the front-right quarter.
CAMERA = (-35.0, 24.0)
PICTURE_PX = 900
PAD = 0.08
EXPLODE_FRACTION = 0.45
TESSELLATION_MM = 0.05
LABEL_COLUMN_PX = 300
# Picture colours. The STEP carries every bought body in magenta (Q29); a
# picture of the circuit tells the parts apart instead.
FORM_COLOURS = {
    "board": (46, 112, 70), "receptacle": (176, 178, 186), "lever-switch": (70, 70, 74),
    "radial-led": (245, 176, 52), "smd-led": (250, 226, 160), "chip": (52, 52, 56),
    "axial": (196, 160, 112), "cylinder": (120, 140, 170), "plate": (200, 196, 180),
    "wire": (210, 60, 40), "box": (150, 150, 150), "envelope": (150, 150, 150),
}
PRINTED_LIGHTEN = 0.55


class Refused(Exception):
    """The inputs cannot be drawn; ``reasons`` names every one."""

    def __init__(self, reasons):
        super().__init__("; ".join(reasons))
        self.reasons = list(reasons)


# ---------------------------------------------------------------------------
# inputs


def run_root(project: Path) -> Path | None:
    for parent in (project, *project.parents):
        if (parent / "WISH.json").is_file():
            return parent
    return None


def sealed_inputs(project: Path) -> tuple[dict, dict]:
    """``(electrical, catalogue)``: the sealed contract's circuit and its
    catalogue snapshot's Bought Parts, from WISH.json above the project."""

    root = run_root(project)
    if root is None:
        raise Refused(["no WISH.json above the CAD project: this tool runs inside a Workshop run"])
    wish = json.loads((root / "WISH.json").read_text(encoding="utf-8"))
    context = wish.get("context") if isinstance(wish, dict) else None
    contract = (context or {}).get("design_contract")
    if (not isinstance(contract, dict) or type(contract.get("schema_version")) is not int
            or contract["schema_version"] < ELECTRICAL_SCHEMA_VERSION
            or not isinstance(contract.get("electrical"), dict)):
        raise Refused(["the sealed contract states no circuit (a schema 10 electrical section)"])
    catalogue = ((context or {}).get("kit_catalogue") or {}).get("bought_parts") or {}
    return contract["electrical"], catalogue


def applies(project: Path) -> bool:
    """Whether final verification draws this run's Bought Parts: a sealed
    schema 10 circuit that is no kit (a kit's Assembly Tree already models
    its Bought Parts, ADR 0092) whose catalogue snapshot records a model for
    one of its parts. A run sealed before catalogue models existed records
    none and keeps what it sealed."""

    try:
        electrical, catalogue = sealed_inputs(project)
    except (Refused, OSError, ValueError):
        return False
    root = run_root(project)
    contract = json.loads((root / "WISH.json").read_text(encoding="utf-8"))["context"]["design_contract"]
    if contract.get("assembly_tree") is not None:
        return False
    return any(isinstance((catalogue.get(item.get("bought")) or {}).get("model"), dict)
               for item in electrical.get("parts") or ())


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _name(part: str, instance: int, count: int) -> str:
    base = OCCURRENCE_PREFIX + part.replace("-", "_")
    return base if count == 1 else "%s_%d" % (base, instance)


def _size(entry: dict, what: str):
    for size in entry.get("sizes") or ():
        if isinstance(size, dict) and size.get("what") == what:
            return [float(v) for v in (size.get("mm") or size.get("max_mm") or ())]
    return None


def _largest_three(entry: dict):
    found = [_size(entry, size.get("what")) for size in entry.get("sizes") or () if isinstance(size, dict)]
    found = [numbers for numbers in found if numbers and len(numbers) == 3]
    return max(found, key=lambda n: n[0] * n[1] * n[2]) if found else None


def _plunger(entry: dict):
    """``(body, plunger, nose length)`` of a catalogue entry that states
    both a ``body`` and a ``plunger`` size, else None. The nose is the
    ``body with plunger out`` height above the body's, or the plunger's own
    length when the entry states no such height."""

    body, plunger = _size(entry, "body"), _size(entry, "plunger")
    if not body or not plunger or len(body) != 3 or len(plunger) != 3:
        return None
    out = _size(entry, "body with plunger out")
    length = out[2] - body[2] if out and len(out) == 3 else plunger[2]
    return body, plunger, round(length, 4)


def read_placements(project: Path) -> tuple[dict, bytes]:
    path = project / PLACEMENTS_PATH
    if not path.is_file():
        raise Refused(["Make wrote no %s: every directional Bought Part needs its facing" % PLACEMENTS_PATH])
    raw = path.read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise Refused(["%s is not JSON" % PLACEMENTS_PATH])
    return document, raw


def _number(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _pose_ok(pose) -> bool:
    if not isinstance(pose, dict) or set(pose) != POSE_KEYS:
        return False
    axis, angle = pose["axis"], pose["angle_deg"]
    return (isinstance(axis, list) and len(axis) == 3 and all(_number(v) for v in axis)
            and math.sqrt(sum(float(v) ** 2 for v in axis)) > 1e-9
            and _number(angle) and 0.0 < abs(angle) <= 180.0)


def check_placements(document) -> list[str]:
    problems = []
    if (not isinstance(document, dict) or document.get("kind") != PLACEMENTS_KIND
            or document.get("schema_version") != SCHEMA_VERSION
            or not set(document) <= {"kind", "schema_version", "parts", "routes"}):
        return ["%s must be {kind: %s, schema_version: 1, parts, routes?}; the board's outline is the "
                "contract's pcba.bounds_mm, never placed here" % (PLACEMENTS_PATH, PLACEMENTS_KIND)]
    parts = document.get("parts", {})
    if not isinstance(parts, dict):
        return ["%s.parts must map part ids to {facing, hinge?, pose?}" % PLACEMENTS_PATH]
    for key, item in sorted(parts.items()):
        if not isinstance(item, dict) or not set(item) <= {"facing", "hinge", "pose"}:
            problems.append("%s.parts.%s must be {facing?, hinge?, pose?}" % (PLACEMENTS_PATH, key))
            continue
        for field in ("facing", "hinge"):
            if field in item and item[field] not in AXES:
                problems.append("%s.parts.%s.%s must be one of %s" % (PLACEMENTS_PATH, key, field, ", ".join(AXES)))
        if "pose" in item and not _pose_ok(item["pose"]):
            problems.append("%s.parts.%s.pose must be {axis: [x, y, z], angle_deg}: a nonzero axis and a "
                            "nonzero angle of at most 180 degrees either way, the right-handed rotation about "
                            "the envelope's centre that turns the world axes into the part's own; a seat "
                            "square to the world axes takes no pose" % (PLACEMENTS_PATH, key))
    routes = document.get("routes", [])
    if not isinstance(routes, list) or len(routes) > MAX_ROUTES:
        problems.append("%s.routes must list at most %d wire routes" % (PLACEMENTS_PATH, MAX_ROUTES))
        routes = []
    for index, route in enumerate(routes):
        where = "%s.routes[%d]" % (PLACEMENTS_PATH, index)
        points = route.get("points") if isinstance(route, dict) else None
        if (not isinstance(route, dict) or set(route) != {"wire", "from", "to", "points"}
                or not isinstance(points, list) or not 2 <= len(points) <= MAX_ROUTE_POINTS
                or any(not isinstance(p, list) or len(p) != 3
                       or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in p)
                       for p in points)):
            problems.append("%s must be {wire, from, to, points} with 2 to %d [x, y, z] points"
                            % (where, MAX_ROUTE_POINTS))
    return problems


def power_envelopes(project: Path) -> tuple[dict, bytes]:
    """``{component id: envelope path}`` from the power report's ``cad.source``."""

    path = project / POWER_PATH
    if not path.is_file():
        raise Refused(["Make wrote no %s: the contract states a circuit" % POWER_PATH])
    raw = path.read_bytes()
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise Refused(["%s is not JSON" % POWER_PATH])
    found = {}
    for item in report.get("components") or () if isinstance(report, dict) else ():
        cad = item.get("cad") if isinstance(item, dict) else None
        if isinstance(cad, dict) and isinstance(cad.get("source"), str) and isinstance(item.get("id"), str):
            found[item["id"]] = cad["source"]
    return found, raw


# ---------------------------------------------------------------------------
# the plan: pure, from envelope bounds


def _unit(axis: str):
    index, sign = AXES[axis]
    vector = [0.0, 0.0, 0.0]
    vector[index] = float(sign)
    return tuple(vector)


def pose_frame(pose: dict, lo, hi) -> dict:
    """A placements ``pose`` with its pivot: the centre of the envelope's
    world bounding box ``(lo, hi)``, which the turn leaves in place."""

    return {"axis": [float(v) for v in pose["axis"]], "angle_deg": float(pose["angle_deg"]),
            "centre": [round((lo[i] + hi[i]) / 2.0, 4) for i in range(3)]}


def _matrix(frame) -> list:
    """The right-handed rotation of ``frame`` (Rodrigues), rows of a 3x3."""

    norm = math.sqrt(sum(v * v for v in frame["axis"]))
    x, y, z = (v / norm for v in frame["axis"])
    angle = math.radians(frame["angle_deg"])
    c, s = math.cos(angle), math.sin(angle)
    t = 1.0 - c
    return [[c + x * x * t, x * y * t - z * s, x * z * t + y * s],
            [y * x * t + z * s, c + y * y * t, y * z * t - x * s],
            [z * x * t - y * s, z * y * t + x * s, c + z * z * t]]


def to_world(frame, vector, point: bool = True):
    """A point (or, with ``point=False``, a direction) of the part's frame in
    the world."""

    m, centre = _matrix(frame), frame["centre"]
    v = [vector[i] - centre[i] for i in range(3)] if point else list(vector)
    out = [sum(m[r][k] * v[k] for k in range(3)) for r in range(3)]
    return tuple(out[i] + centre[i] for i in range(3)) if point else tuple(out)


def to_local(frame, point):
    """A world point in the part's frame: the inverse turn about the pivot."""

    m, centre = _matrix(frame), frame["centre"]
    v = [point[i] - centre[i] for i in range(3)]
    return tuple(sum(m[k][r] * v[k] for k in range(3)) + centre[r] for r in range(3))


def _cells(lo, hi, count: int, skip: int | None):
    """``count`` equal cells of an envelope along its longest axis other than
    ``skip`` (the facing axis), for a part bought several at a time."""

    if count == 1:
        return [(tuple(lo), tuple(hi))]
    extents = [hi[i] - lo[i] for i in range(3)]
    axis = max((i for i in range(3) if i != skip), key=lambda i: (extents[i], -i))
    step = extents[axis] / count
    cells = []
    for n in range(count):
        a, b = list(lo), list(hi)
        a[axis] = lo[axis] + n * step
        b[axis] = lo[axis] + (n + 1) * step
        cells.append((tuple(a), tuple(b)))
    return cells


def _assign(dims, axes, lo, hi):
    """Each of ``dims`` to one of ``axes``: the largest to the envelope's
    longest, deterministically."""

    extents = {i: hi[i] - lo[i] for i in axes}
    order = sorted(axes, key=lambda i: (-extents[i], i))
    return dict(zip(order, sorted(dims, reverse=True)))


def plan_body(form: str, entry: dict, lo, hi, place: dict) -> tuple[dict | None, list[str]]:
    """One body in its envelope cell: ``{"form", "axes": {world axis: size},
    "facing", "hinge", "seat", "bounds", "lever"}``, or None and why."""

    problems = []
    facing = place.get("facing")
    if form in DIRECTIONAL and facing is None:
        return None, ["no facing in %s: a %s is drawn facing the side it works through" % (PLACEMENTS_PATH, form)]
    f_index, f_sign = AXES[facing] if facing else (None, 0)
    cross = [i for i in range(3) if i != f_index]
    sizes: dict[int, float] = {}
    lever = None
    if form in ("envelope", "board"):
        sizes = {i: hi[i] - lo[i] for i in range(3)}
    elif form == "receptacle":
        width, depth, height = _size(entry, "body")
        sizes = {f_index: depth, **_assign([width, height], cross, lo, hi)}
    elif form == "lever-switch":
        length, width, height = _size(entry, "body")
        hinge = place.get("hinge")
        if hinge is None or AXES[hinge][0] == f_index:
            return None, ["a lever switch needs a hinge across its facing in %s" % PLACEMENTS_PATH]
        h_index = AXES[hinge][0]
        (other,) = [i for i in cross if i != h_index]
        sizes = {f_index: height, h_index: length, other: width}
        lever = {"hinge": hinge, "rise_mm": LEVER_RISE_MM, "width_mm": round(min(4.0, 0.7 * width), 4)}
    elif form == "radial-led":
        diameter = _size(entry, "bead diameter")[0]
        sizes = {f_index: _size(entry, "bead height")[0], **{i: diameter for i in cross}}
    elif form in ("smd-led", "chip", "plate"):
        dims = sorted(_size(entry, "plate" if form == "plate" else "body"))
        if facing:
            sizes = {f_index: dims[0], **_assign(dims[1:], cross, lo, hi)}
        else:
            sizes = _assign(dims, range(3), lo, hi)
    elif form == "box" and _plunger(entry) is not None:
        # A push switch: its body, and the plunger as a nose centred on the
        # facing side (issue #228), never one block as tall as both.
        body_dims, plunger, length = _plunger(entry)
        if facing is None:
            return None, ["no facing in %s: a box with a plunger is drawn with its plunger on the side it "
                          "works through" % PLACEMENTS_PATH]
        if length <= 0:
            return None, ["the catalogue's body with plunger out is no taller than its body: the plunger "
                          "has no length to draw"]
        sizes = {f_index: body_dims[2], **_assign(body_dims[:2], cross, lo, hi)}
        order = sorted(cross, key=lambda i: (-sizes[i], i))
        nose = {f_index: length, **dict(zip(order, sorted(plunger[:2], reverse=True)))}
        lever = {"nose_mm": [round(nose[i], 4) for i in range(3)]}
        if sizes[f_index] + length > hi[f_index] - lo[f_index] + FIT_TOLERANCE_MM:
            problems.append("the box body and its plunger are %.2f along %s, its sealed mount envelope only "
                            "%.2f: the catalogue part does not fit the mount"
                            % (sizes[f_index] + length, "xyz"[f_index], hi[f_index] - lo[f_index]))
    elif form == "box":
        dims = sorted(_largest_three(entry))
        if facing:
            sizes = {f_index: dims[0], **_assign(dims[1:], cross, lo, hi)}
        else:
            sizes = _assign(dims, range(3), lo, hi)
    elif form in ("axial", "cylinder"):
        if form == "axial":
            length, diameter = _size(entry, "body")
        else:
            diameter, length = _size(entry, "diameter")[0], _size(entry, "length")[0]
        extents = [hi[i] - lo[i] for i in range(3)]
        along = max(range(3), key=lambda i: (extents[i], -i))
        sizes = {i: (length if i == along else diameter) for i in range(3)}
        lever = {"axis": along}
        if form == "axial":
            sizes[along] = extents[along]          # the leads reach the envelope's ends
            lever.update(body_mm=length, lead_mm=(_size(entry, "lead diameter") or [DEFAULT_LEAD_MM])[0])
    else:
        return None, ["form %s is not one this tool draws" % form]
    for i in range(3):
        if sizes[i] > hi[i] - lo[i] + FIT_TOLERANCE_MM:
            problems.append("the %s body is %.2f along %s, its sealed mount envelope only %.2f: the catalogue "
                            "part does not fit the mount" % (form, sizes[i], "xyz"[i], hi[i] - lo[i]))
    if problems:
        return None, problems
    seat, b_lo, b_hi = [0.0] * 3, [0.0] * 3, [0.0] * 3
    for i in range(3):
        centre = (lo[i] + hi[i]) / 2.0
        if i == f_index:
            back = lo[i] if f_sign > 0 else hi[i]
            seat[i] = back
            far = back + f_sign * sizes[i]
            b_lo[i], b_hi[i] = min(back, far), max(back, far)
        else:
            seat[i] = centre
            b_lo[i], b_hi[i] = centre - sizes[i] / 2.0, centre + sizes[i] / 2.0
    if lever is not None and form == "lever-switch":
        b_lo[f_index] = min(b_lo[f_index], seat[f_index] + f_sign * (sizes[f_index] + LEVER_RISE_MM))
        b_hi[f_index] = max(b_hi[f_index], seat[f_index] + f_sign * (sizes[f_index] + LEVER_RISE_MM))
    if lever is not None and "nose_mm" in lever:
        tip = seat[f_index] + f_sign * (sizes[f_index] + lever["nose_mm"][f_index])
        b_lo[f_index], b_hi[f_index] = min(b_lo[f_index], tip), max(b_hi[f_index], tip)
    body = {"form": form, "size_mm": [round(sizes[i], 4) for i in range(3)], "facing": facing,
            "seat": [round(v, 4) for v in seat],
            "bounds": [[round(v, 4) for v in b_lo], [round(v, 4) for v in b_hi]]}
    if lever is not None:
        body["detail"] = lever
    return body, []


def _reach(point, bounds, frame=None) -> float:
    lo, hi = bounds
    if frame is not None:
        point = to_local(frame, point)
    return math.sqrt(sum(max(lo[i] - point[i], 0.0, point[i] - hi[i]) ** 2 for i in range(3)))


def posed_requests(envelopes: dict, bounds: dict, placements: dict) -> dict:
    """``{part: (envelope path, frame)}`` for every posed part whose
    envelope was read: what ``posed`` bounds ``plan`` needs."""

    found = {}
    for part, place in sorted((placements.get("parts") or {}).items()):
        envelope = envelopes.get(part)
        if isinstance(place, dict) and "pose" in place and envelope in bounds:
            found[part] = (envelope, pose_frame(place["pose"], *bounds[envelope]))
    return found


def plan(electrical: dict, catalogue: dict, envelopes: dict, bounds: dict, placements: dict,
         posed: dict | None = None) -> dict:
    """Every bought body of the circuit, seated in its envelope.

    ``envelopes`` maps a part id to its envelope path, and
    ``bounds`` maps each envelope path to ``(lo, hi)``. ``posed`` maps each
    part with a ``pose`` to its envelope's ``(lo, hi)`` in the part's own
    frame (``posed_requests`` says which). Raises Refused naming every
    problem; the plan is deterministic in its inputs."""

    posed = posed or {}
    problems = []
    places = placements.get("parts", {}) if isinstance(placements, dict) else {}
    board_members = list((electrical.get("pcba") or {}).get("parts") or ())
    bodies = []
    wires = {}
    for item in electrical.get("parts") or ():
        if item.get("external") is True:
            continue
        part, bought = item["id"], item["bought"]
        entry = catalogue.get(bought)
        if entry is None:
            problems.append("%s: %s is not in the sealed catalogue snapshot" % (part, bought))
            continue
        model = entry.get("model") or {}
        form = model.get("form") or ("envelope" if not _largest_three(entry) else "box")
        if not model and entry.get("category") == "wire":
            form = "wire"
        place = places.get(part, {})
        if form == "wire":
            wires[part] = (_size(entry, "lead diameter") or [DEFAULT_LEAD_MM])[0]
            if "pose" in place:
                problems.append("%s: a wire is drawn along its routes and takes no pose" % part)
            continue
        envelope = envelopes.get(part)
        if envelope is None or envelope not in bounds:
            problems.append("%s: the power report seats it in no mount envelope (cad.source), so nothing "
                            "says where it goes" % part)
            continue
        lo, hi = bounds[envelope]
        frame = None
        if "pose" in place:
            frame = pose_frame(place["pose"], lo, hi)
            if part not in posed:
                problems.append("%s: its envelope was not read in the pose's frame" % part)
                continue
            lo, hi = posed[part]
        count = int(item.get("count", 1))
        skip = AXES[place["facing"]][0] if place.get("facing") in AXES else None
        for instance, (c_lo, c_hi) in enumerate(_cells(lo, hi, count, skip), start=1):
            body, why = plan_body(form, entry, c_lo, c_hi, place)
            if body is None:
                problems.extend("%s: %s" % (part, reason) for reason in why)
                continue
            step = model.get("step")
            body.update(name=_name(part, instance, count), part=part, bought=bought, instance=instance,
                        envelope=envelope, on_board=part in board_members,
                        source="vendor" if step else ("envelope" if form == "envelope" else "generated"),
                        licence=step["licence"] if step else None, url=step["url"] if step else None)
            if frame is not None:
                body["pose"] = frame
            bodies.append(body)
    for part in sorted(set(places) - {item["id"] for item in electrical.get("parts") or ()}):
        problems.append("%s places %s, which is no electrical part" % (PLACEMENTS_PATH, part))
    board = (electrical.get("pcba") or {}).get("bounds_mm")
    if board_members:
        # The board is no catalogue part: its outline is the contract's, drawn
        # as stated and never estimated from Make's mounts.
        body, _ = plan_body("board", {}, tuple(board[0]), tuple(board[1]), {})
        body.update(name=OCCURRENCE_PREFIX + BOARD_ID, part=BOARD_ID, bought=None, instance=1,
                    envelope=None, on_board=False, source="contract", licence=None, url=None)
        bodies.append(body)
    where = {}
    for body in bodies:
        where.setdefault(body["part"], []).append((body["bounds"], body.get("pose")))
    routes = []
    for index, route in enumerate(placements.get("routes") or () if isinstance(placements, dict) else ()):
        label = "%s.routes[%d]" % (PLACEMENTS_PATH, index)
        if route.get("wire") not in wires:
            problems.append("%s names %r, which is no wire part of the circuit" % (label, route.get("wire")))
            continue
        for end, point in (("from", route["points"][0]), ("to", route["points"][-1])):
            targets = where.get(route[end])
            if not targets:
                problems.append("%s.%s names %r, which has no body" % (label, end, route[end]))
            elif min(_reach(point, *b) for b in targets) > ROUTE_REACH_MM:
                problems.append("%s starts or ends %.2f from %s; a wire end lies within %.1f of the body it joins"
                                % (label, min(_reach(point, *b) for b in targets), route[end], ROUTE_REACH_MM))
        points = [[round(float(v), 4) for v in p] for p in route["points"]]
        lo = [min(p[i] for p in points) - wires[route["wire"]] / 2 for i in range(3)]
        hi = [max(p[i] for p in points) + wires[route["wire"]] / 2 for i in range(3)]
        routes.append({"name": "%swire_%d" % (OCCURRENCE_PREFIX, index + 1), "form": "wire", "part": route["wire"],
                       "bought": next(i["bought"] for i in electrical["parts"] if i["id"] == route["wire"]),
                       "from": route["from"], "to": route["to"], "points": points,
                       "diameter_mm": wires[route["wire"]], "source": "generated", "licence": None, "url": None,
                       "bounds": [[round(v, 4) for v in lo], [round(v, 4) for v in hi]]})
    if problems:
        raise Refused(problems)
    return {"bodies": bodies, "routes": routes}


# ---------------------------------------------------------------------------
# the Electrical Assembly text and the wiring diagram: pure


def _short(entry: dict | None, part: str, limit: int = 60) -> str:
    name = (entry or {}).get("name") or part
    return name if len(name) <= limit else name[:limit - 1].rstrip() + "…"


def assembly_text(electrical: dict, catalogue: dict) -> str:
    """The toy's Electrical Assembly section, from the contract alone."""

    parts = [item for item in electrical["parts"] if item.get("external") is not True]
    external = [item for item in electrical["parts"] if item.get("external") is True]
    board = set((electrical.get("pcba") or {}).get("parts") or ())
    maker = electrical["assembled_by"] == "maker"
    soldered = electrical["joins"] == "solder"
    who = "the maker" if maker else "the buyer"
    how = "solders" if soldered else "joins without solder"
    supply = electrical["supply_v"]
    lines = ["## Electrical assembly", "",
             "<!-- Written by bought_model.py from the Design Contract's electrical section. -->", ""]
    volts = "%g V nominal, %g to %g V" % (supply["nominal"], supply["min"], supply["max"])
    inlets = [item for item in parts if item["role"] == "inlet"]
    if external:
        through = " through %s (%s)" % (inlets[0]["id"], _short(catalogue.get(inlets[0]["bought"]), inlets[0]["id"], 120)) if inlets else ""
        lines.append("Powered by the buyer's own supply%s (%s). No supply and no battery is in the box." % (through, volts))
    else:
        included = "included" if electrical["batteries_included"] else "not included"
        sources = [item for item in parts if item["role"] == "source"]
        lines.append("Powered by %s (%s); batteries are %s." % (
            ", ".join("%d x %s" % (item.get("count", 1), _short(catalogue.get(item["bought"]), item["id"]))
                      for item in sources), volts, included))
    lines.append("")
    if board:
        on = sum(int(item.get("count", 1)) for item in parts if item["id"] in board)
        off = sum(int(item.get("count", 1)) for item in parts if item["id"] not in board and item["role"] != "wire")
        lines.append("%d parts arrive factory-assembled on one board (PCBA); their joins are made in the "
                     "factory. %s fits the other %d part%s and %s %s wires to the board."
                     % (on, who[0].upper() + who[1:], off, "" if off == 1 else "s", how,
                        "its" if off == 1 else "their"))
    else:
        lines.append("%s fits every part and %s every join." % (who[0].upper() + who[1:], how))
    lines += ["", "Switching: %s" % electrical["switch_logic"].strip(), "",
              "| part | what | count | fitted |", "| --- | --- | --- | --- |"]
    for item in parts:
        fitted = ("on the PCBA, in the factory" if item["id"] in board
                  else "%s, %s" % (who, "soldered" if soldered and item["role"] != "wire" else
                                   "cut to length" if item["role"] == "wire" else "solderless"))
        lines.append("| %s | %s | %d | %s |" % (item["id"], _short(catalogue.get(item["bought"]), item["id"], 90),
                                                int(item.get("count", 1)), fitted))
    lines += ["", "| path | lights | current |", "| --- | --- | --- |"]
    for path in electrical["paths"]:
        lines.append("| %s | %s | %g mA |" % (path["id"], path["load"], path["current_ma"]))
    standby = electrical["standby_ma"]
    lines += ["", "Standby draw: %g mA." % standby if standby else "Standby draw: none; off is open.", ""]
    return "\n".join(lines)


def wiring_layout(electrical: dict) -> dict:
    """Columns of parts in path order and every connection along a path,
    with how it is joined. Pure, so the diagram is deterministic."""

    external = {item["id"] for item in electrical["parts"] if item.get("external") is True}
    board = set((electrical.get("pcba") or {}).get("parts") or ())
    column, order = {}, []
    for path in electrical["paths"]:
        for index, key in enumerate(path["sequence"][:-1]):
            column[key] = max(column.get(key, 0), index)
            if key not in order:
                order.append(key)
    columns: dict[int, list[str]] = {}
    for key in order:
        columns.setdefault(column[key], []).append(key)
    method = "solder" if electrical["joins"] == "solder" else "solderless"
    by = electrical["assembled_by"]
    links, seen = [], set()
    for path in electrical["paths"]:
        sequence = path["sequence"]
        for a, b in zip(sequence[:-1], sequence[1:]):
            pair = (a, b)
            if pair in seen:
                continue
            seen.add(pair)
            if b == sequence[0] and a == sequence[-2]:
                kind = "return"
            elif a in external or b in external:
                kind = "plug"
            elif a in board and b in board:
                kind = "board"
            else:
                kind = method
            links.append({"from": a, "to": b, "kind": kind,
                          "by": "factory" if kind == "board" else "buyer" if kind == "plug" else by})
    return {"columns": [columns[i] for i in sorted(columns)], "links": links,
            "external": sorted(external), "board": sorted(board)}


def _font(size: int):
    from PIL import ImageFont

    return ImageFont.load_default(size=size)


def draw_wiring(electrical: dict, catalogue: dict):
    """The wiring diagram as a PIL image."""

    from PIL import Image, ImageDraw

    layout = wiring_layout(electrical)
    names = {item["id"]: (_short(catalogue.get(item.get("bought")), item["id"], 26)
                          if item.get("external") is not True else "buyer's own supply")
             for item in electrical["parts"]}
    box_w, box_h, gap_x, gap_y, margin = 210, 58, 70, 26, 40
    rows = max(len(column) for column in layout["columns"])
    width = margin * 2 + len(layout["columns"]) * (box_w + gap_x)
    body_h = rows * box_h + (rows - 1) * gap_y
    legend_h = 150 + 22 * len(electrical["paths"])
    height = margin * 2 + 50 + body_h + 60 + legend_h
    image = Image.new("RGB", (max(width, 900), height), (252, 251, 248))
    draw = ImageDraw.Draw(image)
    title, small, tiny = _font(22), _font(15), _font(13)
    draw.text((margin, margin - 10), "Wiring: %d paths from the Design Contract" % len(electrical["paths"]),
              fill=(20, 20, 20), font=title)
    top = margin + 50
    centre = {}
    for c, column in enumerate(layout["columns"]):
        x = margin + c * (box_w + gap_x)
        offset = (body_h - (len(column) * box_h + (len(column) - 1) * gap_y)) / 2
        for r, key in enumerate(column):
            y = top + offset + r * (box_h + gap_y)
            centre[key] = (x, y, x + box_w, y + box_h)
    rail = top + body_h + 34
    bus = margin + len(layout["columns"]) * (box_w + gap_x) - gap_x / 2
    styles = {"board": ((46, 112, 70), 2), "solder": ((214, 96, 30), 4), "solderless": ((40, 90, 190), 4),
              "plug": ((120, 120, 120), 2), "return": ((150, 150, 150), 2)}
    for link in layout["links"]:
        colour, w = styles[link["kind"]]
        a, b = centre[link["from"]], centre.get(link["to"])
        if link["kind"] == "return" or b is None:
            # Every load returns along a bus right of the last column.
            y = (a[1] + a[3]) / 2 + 12
            draw.line([(a[2], y), (bus, y), (bus, rail)], fill=colour, width=w)
            continue
        start = (a[2], (a[1] + a[3]) / 2)
        end = (b[0], (b[1] + b[3]) / 2)
        if b[0] <= a[0]:
            start, end = ((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1])
        mid = end[0] - gap_x / 2 if b[0] > a[0] else (start[0] + end[0]) / 2
        points = [start, (mid, start[1]), (mid, end[1]), end]
        if link["kind"] == "plug":
            for (p, q) in zip(points[:-1], points[1:]):
                segments = 8
                for s in range(0, segments, 2):
                    t0, t1 = s / segments, (s + 1) / segments
                    draw.line([(p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0),
                               (p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1)], fill=colour, width=w)
        else:
            draw.line(points, fill=colour, width=w, joint="curve")
    # Boxes over the lines, so a line passing behind a part stays behind it.
    for key, (x0, y0, x1, y1) in centre.items():
        fill = ((230, 244, 233) if key in layout["board"] else
                (238, 238, 238) if key in layout["external"] else (255, 255, 255))
        outline = (46, 112, 70) if key in layout["board"] else (90, 90, 90)
        draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=2)
        draw.text((x0 + 8, y0 + 6), key, fill=(10, 10, 10), font=small)
        draw.text((x0 + 8, y0 + 30), names.get(key, key), fill=(70, 70, 70), font=tiny)
    source = layout["columns"][0][0]
    left = margin + box_w / 2
    draw.line([(left, centre[source][3]), (left, rail), (bus, rail)], fill=(150, 150, 150), width=2)
    draw.text((left + 8, rail + 6), "return to %s" % source, fill=(90, 90, 90), font=tiny)
    y = rail + 40
    by = "the maker" if electrical["assembled_by"] == "maker" else "the buyer"
    legend = [((46, 112, 70), "board trace: on the factory-assembled PCBA (green boxes)"),
              ((214, 96, 30) if electrical["joins"] == "solder" else (40, 90, 190),
               "wire, %s by %s" % ("soldered" if electrical["joins"] == "solder" else "joined without solder", by)),
              ((120, 120, 120), "plug from the buyer's supply, and the return")]
    for colour, text in legend:
        draw.line([(margin, y + 8), (margin + 50, y + 8)], fill=colour, width=4)
        draw.text((margin + 62, y), text, fill=(30, 30, 30), font=small)
        y += 26
    draw.text((margin, y + 4), "A line is a connection along a stated path, not one solder joint.",
              fill=(90, 90, 90), font=tiny)
    y += 30
    for path in electrical["paths"]:
        draw.text((margin, y), "%s: %s, %g mA, via %s" % (path["id"], path["load"], path["current_ma"],
                                                         " > ".join(path["sequence"][1:-1])),
                  fill=(40, 40, 40), font=tiny)
        y += 22
    return image


def png_bytes(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# geometry (build123d)


_MODULES: dict = {}


def render_review():
    if "render_review" not in _MODULES:
        loader = importlib.machinery.SourceFileLoader("bought_model_render_review", str(RENDER_REVIEW_SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        module._runtime_paths()
        _MODULES["render_review"] = module
    return _MODULES["render_review"]


def envelope_bounds(project: Path, paths) -> dict:
    from build123d import import_step

    found = {}
    for relative in sorted(set(paths)):
        path = project / relative
        if not path.is_file():
            continue
        box = import_step(str(path)).bounding_box()
        found[relative] = ((box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z))
    return found


def _unposed(shape, frame):
    """``shape`` turned back from ``frame``'s pose into the part's frame."""

    from build123d import Axis

    return shape.rotate(Axis(tuple(frame["centre"]), tuple(frame["axis"])), -frame["angle_deg"])


def envelope_posed_bounds(project: Path, requests: dict) -> dict:
    """``{part: (lo, hi)}``: each posed part's envelope bounds in its own
    frame, for ``requests`` as ``posed_requests`` gives them."""

    from build123d import import_step

    found = {}
    for part, (relative, frame) in sorted(requests.items()):
        box = _unposed(import_step(str(project / relative)), frame).bounding_box()
        found[part] = ((box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z))
    return found


def _frame(body):
    """``(origin, x_dir, z_dir)`` of a body's local frame: Z along its
    facing (or the world Z), X along its hinge or long axis."""

    facing = body.get("facing")
    detail = body.get("detail") or {}
    if body["form"] == "lever-switch":
        z = _unit(body["facing"])
        x = _unit(detail["hinge"])
    elif body["form"] in ("axial", "cylinder"):
        axis = detail["axis"]
        x = tuple(1.0 if i == axis else 0.0 for i in range(3))
        z = tuple(1.0 if i == (axis + 1) % 3 else 0.0 for i in range(3))
    elif facing:
        z = _unit(facing)
        f = AXES[facing][0]
        sizes = body["size_mm"]
        cross = [i for i in range(3) if i != f]
        a = max(cross, key=lambda i: (sizes[i], -i))
        x = tuple(1.0 if i == a else 0.0 for i in range(3))
    else:
        z, x = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    return tuple(body["seat"]), x, z


def _local_sizes(body):
    """The body's sizes along its local X, Y and Z."""

    _origin, x, z = _frame(body)
    sizes = body["size_mm"]
    xi = next(i for i in range(3) if x[i])
    zi = next(i for i in range(3) if z[i])
    yi = next(i for i in range(3) if i not in (xi, zi))
    return sizes[xi], sizes[yi], sizes[zi]


def build_shape(body, catalogue_models: Path | None = None):
    """The body as a build123d shape in the assembly frame."""

    from build123d import Align, Box, Cylinder, Location, Plane, Polygon, Pos, Sphere, extrude, import_step

    form = body["form"]
    if form == "wire":
        return _wire_shape(body)
    lx, ly, lz = _local_sizes(body)
    bottom = (Align.CENTER, Align.CENTER, Align.MIN)
    if body.get("source") == "vendor":
        if catalogue_models is None or not (catalogue_models / Path(body["vendor_file"]).name).is_file():
            raise Refused(["%s: the vendor STEP %s is not installed" % (body["name"], body.get("vendor_file"))])
        shape = import_step(str(catalogue_models / Path(body["vendor_file"]).name))
        box = shape.bounding_box()
        shape = shape.moved(Location((-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z)))
    elif form == "receptacle":
        mouth_h = 0.78 * ly
        mouth_w = 0.927 * lx - mouth_h
        depth = 0.75 * lz
        shell = Box(lx, ly, lz, align=bottom)
        pocket = (Pos(0, 0, lz - depth) * Box(mouth_w, mouth_h, depth + 0.01, align=bottom)
                  + Pos(-mouth_w / 2, 0, lz - depth) * Cylinder(mouth_h / 2, depth + 0.01, align=bottom)
                  + Pos(mouth_w / 2, 0, lz - depth) * Cylinder(mouth_h / 2, depth + 0.01, align=bottom))
        tongue = Pos(0, 0, lz - depth) * Box(mouth_w * 0.82, mouth_h * 0.28, depth * 0.85, align=bottom)
        shape = shell - pocket + tongue
    elif form == "lever-switch":
        detail = body["detail"]
        shape = Box(lx, ly, lz, align=bottom)
        run = lx - LEVER_TIP_INSET_MM
        rise = detail["rise_mm"]
        # The hinge sits at local +X (the frame's X is the hinge direction):
        # a strip whose top rises from the body's top there to the free tip
        # LEVER_TIP_INSET_MM in from the other end.
        hinge, tip = lx / 2.0, lx / 2.0 - run
        profile = Polygon((hinge, lz), (tip, lz + rise), (tip, lz + rise - LEVER_THICKNESS_MM),
                          (hinge, lz - LEVER_THICKNESS_MM), align=None)
        shape = shape + extrude(Plane.XZ * profile, amount=detail["width_mm"] / 2.0, both=True)
    elif form == "radial-led":
        diameter = lx
        radius = (diameter - LED_FLANGE_STEP_MM) / 2.0
        flange = Cylinder(diameter / 2.0, LED_FLANGE_MM, align=bottom)
        barrel = max(lz - LED_FLANGE_MM - radius, 0.01)
        shape = (flange + Pos(0, 0, LED_FLANGE_MM) * Cylinder(radius, barrel, align=bottom)
                 + Pos(0, 0, LED_FLANGE_MM + barrel) * Sphere(radius))
        shape = shape & Box(diameter + 1, diameter + 1, lz, align=bottom)
    elif form == "smd-led":
        lens = min(lx, ly) * 0.35
        shape = Box(lx, ly, lz, align=bottom) - Pos(0, 0, lz - 0.1) * Cylinder(lens, 0.2, align=bottom)
    elif form == "axial":
        detail = body["detail"]
        lead = Cylinder(detail["lead_mm"] / 2.0, lx, rotation=(0, 90, 0))
        shape = lead + Cylinder(ly / 2.0, detail["body_mm"], rotation=(0, 90, 0))
    elif form == "cylinder":
        shape = Cylinder(ly / 2.0, lx, rotation=(0, 90, 0))
    elif form == "box" and "nose_mm" in (body.get("detail") or {}):
        # The plunger stands on the body's top (local +Z is the facing),
        # centred across it.
        _origin, x, z = _frame(body)
        nose = body["detail"]["nose_mm"]
        xi = next(i for i in range(3) if x[i])
        zi = next(i for i in range(3) if z[i])
        yi = next(i for i in range(3) if i not in (xi, zi))
        shape = Box(lx, ly, lz, align=bottom) + Pos(0, 0, lz) * Box(nose[xi], nose[yi], nose[zi], align=bottom)
    else:                                      # box, chip, plate, envelope, board
        shape = Box(lx, ly, lz, align=bottom if body.get("facing") else (Align.CENTER,) * 3)
    origin, x, z = _frame(body)
    plane = Plane(origin=origin, x_dir=x, z_dir=z)
    shape = plane.location * shape
    frame = body.get("pose")
    if frame is not None:
        from build123d import Axis

        shape = shape.rotate(Axis(tuple(frame["centre"]), tuple(frame["axis"])), frame["angle_deg"])
    return shape


def _wire_shape(body):
    """One fused solid: an assembly leaf must be one named body, so a wire
    of several segments may not import as nested unnamed children."""

    from build123d import Cylinder, Plane, Pos, Sphere

    radius = body["diameter_mm"] / 2.0
    solids = []
    points = body["points"]
    for a, b in zip(points[:-1], points[1:]):
        vector = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in vector))
        if length < 1e-6:
            continue
        z = tuple(v / length for v in vector)
        helper = (1.0, 0.0, 0.0) if abs(z[0]) < 0.9 else (0.0, 1.0, 0.0)
        x = (helper[1] * z[2] - helper[2] * z[1], helper[2] * z[0] - helper[0] * z[2],
             helper[0] * z[1] - helper[1] * z[0])
        plane = Plane(origin=tuple(a), x_dir=x, z_dir=z)
        solids.append(plane.location * Pos(0, 0, length / 2.0) * Cylinder(radius, length))
    for point in points[1:-1]:
        solids.append(Pos(*point) * Sphere(radius))
    fused = solids[0]
    for solid in solids[1:]:
        fused = fused.fuse(solid)
    return fused.clean()


def _export(shape, name: str, path: Path) -> bytes:
    from build123d import Color, export_step

    shape.label = name
    shape.color = Color(1.0, 0.0, 1.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, str(path))
    return path.read_bytes()


GROUP_MODULE = '''"""The toy's Bought Parts as one group (ADR 0095 amendment, 2026-11-01).

Written by make-round/scripts/bought_model.py --build; do not edit. Add
``bought_group()`` to the assembly entry's compound so the assembled STEP
carries every Bought Part, named ``bought_<part>``, in the reserved
not-printed magenta. These bodies are no print part: none is a ``part_*``
entry and none gets a ``parts/`` production STEP.
"""

import hashlib
from pathlib import Path

BODIES = %s


def bought_group(label="%s"):
    from build123d import Color, Compound, import_step

    here = Path(__file__).resolve().parent
    children = []
    for name, file, sha256 in BODIES:
        data = (here / file).read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError("bought body %%s changed since bought_model.py wrote it" %% file)
        # One leaf per body: a STEP of several solids (a vendor model) is
        # flattened, never nested as unnamed children.
        solids = import_step(str(here / file)).solids()
        shape = solids[0] if len(solids) == 1 else Compound(list(solids))
        shape.label = name
        shape.color = Color(1.0, 0.0, 1.0)
        children.append(shape)
    return Compound(label=label, children=children)
'''


def _inputs(project: Path, electrical: dict, catalogue: dict, power_raw: bytes, placements_raw: bytes,
            envelope_paths) -> dict:
    used = {item["bought"]: catalogue.get(item["bought"]) for item in electrical["parts"] if "bought" in item}
    return {
        "electrical_sha256": _sha(_canonical(electrical)),
        "catalogue_sha256": _sha(_canonical(used)),
        "power_sha256": _sha(power_raw),
        "placements_sha256": _sha(placements_raw),
        "envelopes": {path: _sha((project / path).read_bytes()) for path in sorted(set(envelope_paths))
                      if (project / path).is_file()},
    }


def prepare(project: Path, bounds_reader=envelope_bounds,
            posed_reader=envelope_posed_bounds) -> tuple[dict, dict, dict, dict]:
    """``(electrical, catalogue, plan, inputs)`` for the project. A pose is
    part of the placements file's bytes, so ``placements_sha256`` binds it."""

    electrical, catalogue = sealed_inputs(project)
    placements, placements_raw = read_placements(project)
    problems = check_placements(placements)
    if problems:
        raise Refused(problems)
    envelopes, power_raw = power_envelopes(project)
    paths = list(envelopes.values())
    bounds = bounds_reader(project, paths)
    requests = posed_requests(envelopes, bounds, placements)
    posed = posed_reader(project, requests) if requests else {}
    planned = plan(electrical, catalogue, envelopes, bounds, placements, posed)
    for body in planned["bodies"]:
        step = (catalogue.get(body["bought"]) or {}).get("model", {}).get("step") if body["bought"] else None
        if step:
            body["vendor_file"] = step["file"]
            body["vendor_sha256"] = step["sha256"]
    return electrical, catalogue, planned, _inputs(project, electrical, catalogue, power_raw, placements_raw, paths)


def build(project: Path, catalogue_models: Path | None = None) -> dict:
    """Write every body, the group module and the body list."""

    _electrical, _catalogue, planned, inputs = prepare(project)
    render_review()._runtime_paths()
    directory = project / BOUGHT_DIR
    directory.mkdir(exist_ok=True)
    for stale in directory.glob("*.step"):
        stale.unlink()
    listed = []
    for body in planned["bodies"] + planned["routes"]:
        data = _export(build_shape(body, catalogue_models), body["name"], directory / ("%s.step" % body["name"]))
        body["step"] = "%s/%s.step" % (BOUGHT_DIR, body["name"])
        body["step_sha256"] = _sha(data)
        listed.append((body["name"], "%s.step" % body["name"], body["step_sha256"]))
    literal = "(\n" + "".join("    %r,\n" % (item,) for item in listed) + ")"
    module = GROUP_MODULE % (literal, GROUP_LABEL)
    (directory / "__init__.py").write_text(module, encoding="utf-8")
    document = {"kind": BODIES_KIND, "schema_version": SCHEMA_VERSION, "inputs": inputs,
                "group": GROUP_LABEL, "colour": BOUGHT_PART_HEX,
                "module_sha256": _sha(module.encode("utf-8")), **planned}
    path = project / BODIES_PATH
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return document


def check_built(project: Path, document: dict, planned: dict, inputs: dict, measure=None) -> list[str]:
    """Why the written bodies are not the plan of the current inputs."""

    problems = []
    if document.get("kind") != BODIES_KIND or document.get("schema_version") != SCHEMA_VERSION:
        return ["%s is not a bought-bodies list; run bought_model.py --build" % BODIES_PATH]
    if document.get("inputs") != inputs:
        changed = sorted(key for key in inputs if document.get("inputs", {}).get(key) != inputs[key])
        problems.append("the inputs changed since --build (%s); run bought_model.py --build again" % ", ".join(changed))

    def strip(items):
        return [{k: v for k, v in item.items() if k not in ("step", "step_sha256")} for item in items]

    for key in ("bodies", "routes"):
        if strip(document.get(key) or []) != strip(planned[key]):
            problems.append("%s.%s is not the plan of the current inputs" % (BODIES_PATH, key))
    module = project / BOUGHT_DIR / "__init__.py"
    if not module.is_file() or _sha(module.read_bytes()) != document.get("module_sha256"):
        problems.append("%s/__init__.py changed since --build" % BOUGHT_DIR)
    for body in (document.get("bodies") or []) + (document.get("routes") or []):
        path = project / str(body.get("step"))
        if not path.is_file() or _sha(path.read_bytes()) != body.get("step_sha256"):
            problems.append("%s changed since --build" % body.get("step"))
        elif measure is not None:
            # A posed body is measured turned back into its own frame,
            # where its plan's bounds are.
            lo, hi = measure(path) if body.get("pose") is None else measure(path, body["pose"])
            want_lo, want_hi = body["bounds"]
            if any(abs(lo[i] - want_lo[i]) > BOUND_TOLERANCE_MM + 1e-9 or abs(hi[i] - want_hi[i]) > BOUND_TOLERANCE_MM + 1e-9
                   for i in range(3)) and body["form"] != "wire":
                problems.append("%s is not where the plan seats %s" % (body["step"], body["name"]))
    return problems


def _step_bounds(path: Path, frame=None):
    from build123d import import_step

    shape = import_step(str(path))
    box = (shape if frame is None else _unposed(shape, frame)).bounding_box()
    return (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z)


# ---------------------------------------------------------------------------
# pictures


class Mesh:
    def __init__(self, points, faces, colour):
        import numpy as np

        self.points = np.asarray(points, dtype=float)
        self.faces = np.asarray(faces, dtype=np.int64)
        self.colour = tuple(int(c) for c in colour)


def _is_magenta(colour) -> bool:
    return colour[0] >= 240 and colour[1] <= 15 and colour[2] >= 240


def cad_meshes(project: Path, document: dict) -> tuple[list, dict]:
    """``(printed meshes, {body name: mesh})``: the printed parts from the
    assembly STEP (bought magenta leaves left out) and each bought body."""

    import numpy as np
    from build123d import import_step

    review = render_review()
    entries = [p for p in sorted(project.glob("*.step.py")) if not p.name.startswith("part_")]
    printed = []
    if len(entries) == 1 and entries[0].with_suffix("").is_file():
        shape = import_step(str(entries[0].with_suffix("")))
        for points, faces, colour in review.tessellate_occurrences(shape, TESSELLATION_MM * 4):
            colour = tuple(int(c) for c in colour)
            if not _is_magenta(colour):
                printed.append(Mesh(points, faces, colour))
    bodies = {}
    for body in document["bodies"] + document["routes"]:
        occurrences = review.tessellate_occurrences(import_step(str(project / body["step"])), TESSELLATION_MM)
        points = np.concatenate([o[0] for o in occurrences])
        offset, faces = 0, []
        for o in occurrences:
            faces.append(np.asarray(o[1]) + offset)
            offset += len(o[0])
        bodies[body["name"]] = Mesh(points, np.concatenate(faces), FORM_COLOURS.get(body["form"], (150, 150, 150)))
    return printed, bodies


def _projector(points, size: int):
    import numpy as np

    review = render_review()
    _toward, right, up = review.camera_basis(*CAMERA)
    sx, sy = points @ right, points @ up
    width, height = float(sx.max() - sx.min()), float(sy.max() - sy.min())
    span = max(width, height, 1e-9)
    scale = (1.0 - 2.0 * PAD) * size / span
    x_offset = (size - width * scale) / 2.0 - float(sx.min()) * scale
    y_offset = (size - height * scale) / 2.0 + float(sy.max()) * scale

    def project(point):
        point = np.asarray(point, dtype=float)
        return float(point @ right * scale + x_offset), float(y_offset - point @ up * scale)

    return project


def _labelled(scene, labels, size: int):
    """Shade ``scene`` (``[(points, faces, colour)]``) and add a label column
    with a leader to each ``(text, point)``."""

    import numpy as np
    from PIL import Image, ImageDraw

    review = render_review()
    framing = np.concatenate([points for points, _faces, _colour in scene])
    shaded = review.render(scene, CAMERA[0], CAMERA[1], size, PAD, framing=framing)
    project = _projector(framing, size)
    image = Image.new("RGB", (size + LABEL_COLUMN_PX, size), tuple(review.BACKGROUND))
    image.paste(shaded, (0, 0))
    draw = ImageDraw.Draw(image)
    font = _font(14)
    placed = sorted(((project(point), text) for text, point in labels), key=lambda item: (item[0][1], item[1]))
    if placed:
        step = max(18, min(34, (size - 40) // max(len(placed), 1)))
        top = max(20, (size - step * len(placed)) // 2)
        for n, ((x, y), text) in enumerate(placed):
            label_y = top + n * step
            draw.line([(x, y), (size + 6, label_y + 8)], fill=(90, 90, 90), width=1)
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(200, 40, 40))
            draw.text((size + 10, label_y), text, fill=(20, 20, 20), font=font)
    return image


def _label(body) -> str:
    return body["part"] if body.get("instance", 1) == 1 or body["form"] == "wire" else "%s #%d" % (
        body["part"], body["instance"])


def pictures(document: dict, printed: list, bodies: dict) -> dict:
    """The exploded and cut-away pictures, by name."""

    import numpy as np

    review = render_review()
    toward, _right, _up = review.camera_basis(*CAMERA)
    every = document["bodies"] + document["routes"]
    all_points = np.concatenate([bodies[b["name"]].points for b in every])
    span = float(np.max(all_points.max(axis=0) - all_points.min(axis=0)))
    centre = (all_points.min(axis=0) + all_points.max(axis=0)) / 2.0
    exploded, labels = [], []
    for body in every:
        mesh = bodies[body["name"]]
        if body["form"] == "board":
            shift = np.zeros(3)
        elif body.get("facing"):
            direction = _unit(body["facing"])
            if body.get("pose") is not None:
                direction = to_world(body["pose"], direction, point=False)
            shift = np.asarray(direction) * EXPLODE_FRACTION * span
        else:
            middle = (mesh.points.min(axis=0) + mesh.points.max(axis=0)) / 2.0
            away = middle - centre
            norm = float(np.linalg.norm(away))
            shift = (away / norm if norm > 1e-6 else np.zeros(3)) * EXPLODE_FRACTION * span * 0.6
        points = mesh.points + shift
        exploded.append((points, mesh.faces, mesh.colour))
        if body["form"] != "wire":
            labels.append((_label(body), (points.min(axis=0) + points.max(axis=0)) / 2.0))
    images = {"exploded": _labelled(exploded, labels, PICTURE_PX)}
    # The cut: every printed triangle on the camera's side of the vertical
    # plane through the bought parts' centre is left out.
    normal = np.asarray([toward[0], toward[1], 0.0])
    normal = normal / max(float(np.linalg.norm(normal)), 1e-9)
    scene, labels = [], []
    for mesh in printed:
        middles = mesh.points[mesh.faces].mean(axis=1)
        keep = (middles - centre) @ normal <= 0.0
        if keep.any():
            scene.append((mesh.points, mesh.faces[keep], tuple(
                int(c + (255 - c) * PRINTED_LIGHTEN) for c in mesh.colour)))
    for body in every:
        mesh = bodies[body["name"]]
        scene.append((mesh.points, mesh.faces, mesh.colour))
        if body["form"] != "wire":
            labels.append((_label(body), (mesh.points.min(axis=0) + mesh.points.max(axis=0)) / 2.0))
    images["cutaway"] = _labelled(scene, labels, PICTURE_PX)
    return images


def final(project: Path, meshes=None) -> dict:
    """Check the written bodies, then write the pictures and the text."""

    electrical, catalogue, planned, inputs = prepare(project)
    path = project / BODIES_PATH
    if not path.is_file():
        raise Refused(["no %s: run bought_model.py --build and add bought_group() to the assembly" % BODIES_PATH])
    document = json.loads(path.read_text(encoding="utf-8"))
    problems = check_built(project, document, planned, inputs, measure=_step_bounds if meshes is None else None)
    if problems:
        raise Refused(problems)
    printed, bodies = cad_meshes(project, document) if meshes is None else meshes
    images = pictures(document, printed, bodies)
    images["wiring"] = draw_wiring(electrical, catalogue)
    out = project / ELECTRICAL_DIR
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ("exploded", "cutaway", "wiring"):
        data = png_bytes(images[name])
        (out / ("%s.png" % name)).write_bytes(data)
        files["%s.png" % name] = _sha(data)
    text = assembly_text(electrical, catalogue)
    (out / "assembly.md").write_text(text, encoding="utf-8")
    files["assembly.md"] = _sha(text.encode("utf-8"))
    report = {"kind": ELECTRICAL_KIND, "schema_version": SCHEMA_VERSION,
              "bodies_sha256": _sha(path.read_bytes()), "files": files,
              "bodies": [b["name"] for b in document["bodies"] + document["routes"]],
              "layout": wiring_layout(electrical)}
    (out / "electrical.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true", help="draw every Bought Part body and the bought group")
    mode.add_argument("--final", action="store_true", help="check the bodies and write the electrical pictures")
    mode.add_argument("--applies", action="store_true", help="exit 0 when this run draws its Bought Parts, else 3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if args.applies:
        return 0 if applies(project) else 3
    try:
        result = build(project) if args.build else final(project)
    except Refused as refused:
        for reason in refused.reasons:
            print("bought_model: %s" % reason, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        names = [b["name"] for b in result.get("bodies", [])] if args.build else result["bodies"]
        print("bought_model: %s %d bought bodies: %s" % ("wrote" if args.build else "checked and drew",
                                                        len(names) + (len(result.get("routes", [])) if args.build else 0),
                                                        ", ".join(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
