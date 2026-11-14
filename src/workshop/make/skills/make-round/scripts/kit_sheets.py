#!/usr/bin/env python3
"""A kit's FDM Sheets and their checks (Workshop ADR 0104 decisions 1 and 3).

    kit_sheets.py describe <project>/sheet_<id>.py
    kit_sheets.py check <project> [--kit KIT.json]

``check`` reads the installed tree (``tree/kit.json``), or the kit install
document ``--kit`` names (``make_round --print-gates-only --contract``); with no Sheets it
passes and checks nothing. Otherwise it builds every Sheet and every kit
Component's ``print_parts()``, runs :func:`check` and
:func:`part_failures`, prints one ``FAIL`` line per failure and a JSON
report line, ``{"kind": "kit-sheets-report", "verdict", "failures",
"small", "sheets"}``, and exits 1 on any failure.

A **Sheet** is one printed plate of one filament: a frame of runners that
carries printed Parts by break-off gates. Its file defines ``sheet()``,
returning::

    {"frame": shape,                 # runners, tags and debossed ids, fused
     "parts": [{"id": Part id,       # one entry per copy on the plate
                "shape": shape,      # the copy in its print stance, on the bed
                "gates": [{"shape": shape,     # the gate bar, runner to Part
                           "x": float, "y": float,  # the cut point on the outline
                           "d": +1 or -1}]}]}  # +1: runner below the Part

``describe`` builds it once and prints one JSON line, ``{"kind":
"kit-sheet", ...}``, with each copy's measures and plan footprint and each
gate's bar, all as plan polygons (WKT). :func:`check` then gates it without
the CAD kernel, with the constants the owner reviewed on the Amsterdam kit's
own ``sheets.py`` (2026-11-14):

- **Same Parts.** The copies are exactly the Sheet's contract entries, each
  equal in volume and area to that Part's ``print_parts()`` shape, on the
  bed.
- **Flat plate.** No copy is over 3.0 mm tall.
- **One bed.** The whole Sheet, frame, gates and copies, fits in plan
  within 250 x 250 mm: Factory's printer (Bambu A1) has a 256 mm bed, less
  3 mm a side. A larger Sheet is printed on no plate.
- **Separable.** Each copy is at least 2.0 mm from the frame and every other
  copy, touches each of its gates and has at least one; each gate touches
  the frame.
- **Nipper access.** Each gate's jaw keep-out, 6.0 mm to each side of its
  centre line and 2.0 mm back from the cut point, is free of every copy, the
  frame and the other gates, and the cut lands on a straight or convex edge
  across the bar's width.
- **Fragile tips.** A tip narrower than 1.6 mm 0.3 mm behind its apex, or
  narrowing to under 0.6 of its width 1.5 mm behind, has no gate within
  3 mm, no copy or frame within 3 mm and no frame or gate within 8 mm
  straight ahead.

:func:`part_failures` holds every printed Part of a kit with Sheets, loose
or not, to the minimum size (owner rule MIN-PART-SIZE R1, on the sorted
print-stance size: thickness 1.6, short side 4, long side 8, footprint
short x long 35 mm2, volume 50 mm3) unless it states ``small_reason``, and
asks a spare on its Sheets of each Part under 15 mm long.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

CAD_SCRIPTS = Path(__file__).resolve().parents[2] / "cad" / "scripts"
KIND = "kit-sheet"
FUNCTION = "sheet"

BED_TOLERANCE_MM = 0.01
SAME_TOLERANCE = 1e-4            # relative volume and area of a copy against its print_parts() shape
MAX_HEIGHT_MM = 3.0              # a Sheet is a flat plate
BED_MM = 256.0                   # Factory's printer (Bambu A1)
BED_MARGIN_MM = 3.0              # kept clear at each edge of the bed
SHEET_MAX_MM = BED_MM - 2 * BED_MARGIN_MM
SEPARATION_MM = 2.0              # a copy to the frame and to every other copy, away from its gates
TOUCH_MM = 1e-3
JAW_HALF, JAW_D = 6.0, 2.0       # the nipper's keep-out at a cut point
SEAT_TOL = 1.0                   # a round end falls under the bar by less than this
TIP_DROP, TIP_SPAN = 1.9, 2.0    # a point steeper than 45 deg each side; a round end (r >= 2) is no tip
TIP_CLEAR, TIP_NEAR = 3.0, 8.0   # free space round a fragile apex, and straight ahead of it
AREA_EPS = 0.01
# MIN-PART-SIZE R1 and the spare rule.
MIN_THICK, MIN_SHORT, MIN_LONG, MIN_FOOT, MIN_VOLUME = 1.6, 4.0, 8.0, 35.0, 50.0
SPARE_BELOW_MM = 15.0

RULE = ("a Sheet file defines sheet() returning {frame: shape, parts: [{id, shape, gates: [{shape, x, y, d}]}]}: "
        "the frame of runners and tags, every Part copy in its print stance on the bed, and each copy's gate "
        "bars with their cut point on its outline, d +1 when the runner is below (ADR 0104)")


def _runtime_paths() -> None:
    for path in (CAD_SCRIPTS, CAD_SCRIPTS / "packages", CAD_SCRIPTS / "packages" / "cadgen" / "src"):
        text = str(path)
        if path.is_dir() and text not in sys.path:
            sys.path.insert(0, text)


# ---------------------------------------------------------------------------
# describe: the build side


def footprint(shape):
    """The plan outline of a flat shape: the union of its horizontal planar faces."""

    from build123d import GeomType
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def ring(wire):
        points = []
        for edge in wire.edges():
            steps = max(2, int(edge.length / 0.25))
            points += [(p.X, p.Y) for p in (edge.position_at(i / steps) for i in range(steps))]
        return points

    polygons = []
    for face in shape.faces():
        if face.geom_type != GeomType.PLANE or abs(abs(face.normal_at().Z) - 1) > 1e-6:
            continue
        try:
            polygons.append(Polygon(ring(face.outer_wire()), [ring(w) for w in face.inner_wires()]).buffer(0))
        except Exception:  # noqa: BLE001 - a degenerate face adds no plan area
            continue
    return unary_union(polygons).buffer(0.01).buffer(-0.01)


def _measures(shape) -> dict:
    box = shape.bounding_box()
    return {"volume": round(float(shape.volume), 4), "area": round(float(shape.area), 4),
            "size": sorted(round(float(v), 3) for v in (box.size.X, box.size.Y, box.size.Z)),
            "bottom": round(float(box.min.Z), 4), "top": round(float(box.max.Z), 4)}


def describe(entry: Path) -> dict:
    _runtime_paths()
    from build123d import Shape

    from printlib import detail_build, load_entry, project_on_path

    with project_on_path(entry.parent), contextlib.redirect_stdout(io.StringIO()), detail_build():
        module = load_entry(entry, "kit_sheets")
        builder = getattr(module, FUNCTION, None)
        if not callable(builder):
            return {"kind": KIND, "error": "%s defines no sheet()" % entry.name}
        built = builder()
    if not isinstance(built, dict) or not isinstance(built.get("frame"), Shape) \
            or not isinstance(built.get("parts"), list) or not built["parts"]:
        return {"kind": KIND, "error": "sheet() did not return a frame shape and a list of parts"}
    frame = built["frame"]
    copies = []
    for index, item in enumerate(built["parts"]):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) \
                or not isinstance(item.get("shape"), Shape) or not isinstance(item.get("gates"), list):
            return {"kind": KIND, "error": "sheet() parts[%d] is not {id, shape, gates}" % index}
        for number, gate in enumerate(item["gates"]):
            if not isinstance(gate, dict) or not isinstance(gate.get("shape"), Shape) \
                    or not all(isinstance(gate.get(k), (int, float)) for k in ("x", "y")) or gate.get("d") not in (1, -1):
                return {"kind": KIND, "error": "sheet() parts[%d] gate %d is not {shape, x, y, d: +1 or -1}"
                        % (index, number)}
        copies.append(item)
    parts = []
    for index, item in enumerate(copies):
        shape = item["shape"]
        others = [other["shape"] for j, other in enumerate(copies) if j != index]
        parts.append({
            "id": item["id"], **_measures(shape), "footprint": footprint(shape).wkt,
            "to_frame": round(float(shape.distance_to(frame)), 3),
            "to_part": round(min((float(shape.distance_to(o)) for o in others), default=99.0), 3),
            "gates": [{"x": float(g["x"]), "y": float(g["y"]), "d": int(g["d"]),
                       "bar": footprint(g["shape"]).wkt if footprint(g["shape"]).area > 0
                       else _plan_box(g["shape"]),
                       "touches_part": float(g["shape"].distance_to(shape)) < TOUCH_MM,
                       "touches_frame": float(g["shape"].distance_to(frame)) < TOUCH_MM}
                      for g in item["gates"]]})
    return {"kind": KIND, "error": None, "frame": {"footprint": footprint(frame).wkt, **_measures(frame)},
            "parts": parts}


def _plan_box(shape) -> str:
    from shapely.geometry import box

    b = shape.bounding_box()
    return box(b.min.X, b.min.Y, b.max.X, b.max.Y).wkt


def parse(stdout: str, returncode: int) -> dict:
    """A ``describe`` run's result from its JSON line."""

    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            break
        if isinstance(payload, dict) and payload.get("kind") == KIND:
            return payload
        break
    return {"kind": KIND, "error": "sheet() did not build (kit_sheets.py exit %d)" % returncode}


# ---------------------------------------------------------------------------
# check: plan geometry only


def _edge_hit(fp, x, d):
    """The first material of ``fp`` met along x from the runner side."""

    from shapely.geometry import LineString

    b = fp.bounds
    seg = fp.intersection(LineString([(x, b[1] - 1), (x, b[3] + 1)]))
    if seg.is_empty:
        return None
    return seg.bounds[1] if d > 0 else seg.bounds[3]


def keepout(x, cut, d):
    from shapely.geometry import box

    return box(x - JAW_HALF, cut - JAW_D, x + JAW_HALF, cut - 0.05) if d > 0 \
        else box(x - JAW_HALF, cut + 0.05, x + JAW_HALF, cut + JAW_D)


def flat_edge(fp, x, cut, d, half) -> bool:
    """The cut lands on straight or convex edge: the bar's width (+0.3 a side)
    meets the Part within SEAT_TOL of the cut point."""

    for q in (x - half, x - half / 2, x + half / 2, x + half):
        hit = _edge_hit(fp, q, d)
        if hit is None or (hit - cut) * d > SEAT_TOL or (cut - hit) * d > 0.05:
            return False
    return True


def _grid(bounds, step=0.25):
    count = int((bounds[2] - bounds[0] - 0.6) / step)
    return [bounds[0] + 0.3 + i * step for i in range(count + 1)]


def _tips(fp, xs):
    """Apexes facing -y: local extremes of the edge profile that fall back at
    least TIP_DROP within TIP_SPAN on each side."""

    profile = [(x, _edge_hit(fp, x, 1)) for x in xs]
    profile = [(x, h) for x, h in profile if h is not None]
    found = []
    for x, h in profile:
        near = [hh for xx, hh in profile if 0 < abs(xx - x) <= TIP_SPAN + 1e-6]
        if not near:
            continue
        left = [hh - h for xx, hh in profile if 0 < x - xx <= TIP_SPAN + 1e-6]
        right = [hh - h for xx, hh in profile if 0 < xx - x <= TIP_SPAN + 1e-6]
        if all(hh - h >= -1e-6 for hh in near) and max(left, default=TIP_DROP + 1) >= TIP_DROP \
                and max(right, default=TIP_DROP + 1) >= TIP_DROP:
            if not found or abs(found[-1][0] - x) > TIP_SPAN:
                found.append((x, h))
            elif h < found[-1][1]:
                found[-1] = (x, h)
    return found


# Each direction's plan transform (shapely affine [a, b, d, e, xoff, yoff])
# turning that direction into -y, and the unit vector of the direction.
_TURN = {"down": [1, 0, 0, 1, 0, 0], "up": [1, 0, 0, -1, 0, 0], "left": [0, 1, 1, 0, 0, 0], "right": [0, 1, -1, 0, 0, 0]}
_AHEAD = {"down": (0, -1), "up": (0, 1), "left": (-1, 0), "right": (1, 0)}


def _chord(fp, x, y):
    from shapely.geometry import LineString

    seg = fp.intersection(LineString([(x - 6, y), (x + 6, y)]))
    for piece in getattr(seg, "geoms", [seg]):
        if not piece.is_empty and piece.bounds[0] - 1e-6 <= x <= piece.bounds[2] + 1e-6:
            return piece.length
    return 0.0


def fragile_tips(fp):
    """``[(x, y, direction)]``: every fragile apex of a plan footprint."""

    from shapely import affinity

    found = []
    for direction, matrix in _TURN.items():
        turned = affinity.affine_transform(fp, matrix)
        for x, h in _tips(turned, _grid(turned.bounds)):
            w03, w15 = _chord(turned, x, h + 0.3), _chord(turned, x, h + 1.5)
            if w03 < 1.6 or (w15 < 3.0 and w03 < 0.6 * w15):
                found.append({"down": (x, h), "up": (x, -h), "left": (h, x), "right": (-h, x)}[direction]
                             + (direction,))
    return found


def _same(a, b) -> bool:
    return abs(a - b) <= SAME_TOLERANCE * max(abs(a), abs(b), 1.0)


def check(described: dict, spec: dict, measures: dict) -> list[str]:
    """Every way one described Sheet breaks its contract entry ``spec``
    (``{id, filament, parts: [{id, count}]}``); ``measures`` maps each Part
    id to its ``print_parts()`` volume and area. Each line is a repair."""

    from shapely import wkt
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union

    name = "sheet_%s.py" % spec["id"]
    if not isinstance(described, dict) or described.get("error") or not described.get("parts"):
        why = (described or {}).get("error") if isinstance(described, dict) else None
        return ["%s: %s; %s" % (name, why or "sheet() was not described", RULE)]
    fails = []
    parts = described["parts"]
    counted = {}
    for item in parts:
        counted[item["id"]] = counted.get(item["id"], 0) + 1
    wanted = {entry["id"]: entry["count"] for entry in spec["parts"]}
    for part in sorted(set(counted) | set(wanted)):
        if counted.get(part, 0) != wanted.get(part, 0):
            fails.append("%s: holds %d x %s, but the contract's Sheet %s lists %d"
                         % (name, counted.get(part, 0), part, spec["id"], wanted.get(part, 0)))
    for item in parts:
        reference = measures.get(item["id"])
        if reference and not (_same(item["volume"], reference["volume"]) and _same(item["area"], reference["area"])):
            fails.append("%s: a copy of %s is %.1f mm3 / %.1f mm2, but print_parts() builds it at %.1f mm3 / "
                         "%.1f mm2: place the Part's own print_parts() shape on the Sheet"
                         % (name, item["id"], item["volume"], item["area"], reference["volume"], reference["area"]))
        if abs(item["bottom"]) > BED_TOLERANCE_MM:
            fails.append("%s: a copy of %s has its bottom at Z %.3f, not on the bed" % (name, item["id"], item["bottom"]))
        if item["top"] - item["bottom"] > MAX_HEIGHT_MM + 1e-6:
            fails.append("%s: a copy of %s is %.1f mm tall; a Sheet is a flat plate, at most %.1f mm: print it "
                         "loose with a loose_reason" % (name, item["id"], item["top"] - item["bottom"], MAX_HEIGHT_MM))
        if item["to_frame"] < SEPARATION_MM or item["to_part"] < SEPARATION_MM:
            fails.append("%s: a copy of %s is %.2f mm from the frame and %.2f mm from another Part, under %.1f"
                         % (name, item["id"], item["to_frame"], item["to_part"], SEPARATION_MM))
        if not item["gates"]:
            fails.append("%s: a copy of %s has no gate" % (name, item["id"]))
        for gate in item["gates"]:
            if not gate["touches_part"] or not gate["touches_frame"]:
                fails.append("%s: the gate of %s at x %.1f does not join %s"
                             % (name, item["id"], gate["x"],
                                " and ".join(w for w, ok in (("the Part", gate["touches_part"]),
                                                             ("the frame", gate["touches_frame"])) if not ok)))
    footprints = [wkt.loads(item["footprint"]) for item in parts]
    frame = wkt.loads(described["frame"]["footprint"])
    gates = [(index, gate, wkt.loads(gate["bar"])) for index, item in enumerate(parts) for gate in item["gates"]]
    every_part = unary_union(footprints)
    for number, (index, gate, bar) in enumerate(gates):
        own = footprints[index]
        cut = gate["y"]
        zone = keepout(gate["x"], cut, gate["d"])
        others = unary_union([b for n, (_, _, b) in enumerate(gates) if n != number])
        hits = [what for what, area in (("a Part", zone.intersection(every_part).area),
                                        ("the frame", zone.intersection(frame).area),
                                        ("another gate", zone.intersection(others).area)) if area > AREA_EPS]
        half = (bar.bounds[2] - bar.bounds[0]) / 2 + 0.3
        if not flat_edge(own, gate["x"], cut, gate["d"], half):
            hits.append("an edge that is not straight or convex")
        if hits:
            fails.append("%s: the nipper cannot reach the gate of %s at x %.1f: its jaw keep-out (%.0f mm a side, "
                         "%.0f mm back) meets %s" % (name, parts[index]["id"], gate["x"], JAW_HALF, JAW_D,
                                                     ", ".join(hits)))
    bars = unary_union([bar for _, _, bar in gates])
    fails += bed_failures(name, unary_union([frame, every_part, bars]))
    for index, own in enumerate(footprints):
        others = unary_union([fp for n, fp in enumerate(footprints) if n != index])
        for x, y, direction in fragile_tips(own):
            disk = Point(x, y).buffer(TIP_CLEAR)
            dx, dy = _AHEAD[direction]
            ray = LineString([(x + dx * 0.05, y + dy * 0.05), (x + dx * TIP_NEAR, y + dy * TIP_NEAR)])
            why = []
            if bars.intersects(disk):
                why.append("a gate within %.0f mm" % TIP_CLEAR)
            if ray.intersects(frame) or ray.intersects(bars):
                why.append("the frame or a gate within %.0f mm ahead" % TIP_NEAR)
            if disk.intersection(frame).area > AREA_EPS or disk.intersection(others).area > AREA_EPS:
                why.append("the frame or a Part within %.0f mm" % TIP_CLEAR)
            if why:
                fails.append("%s: the fragile tip of %s at (%.1f, %.1f) pointing %s has %s: turn it into open "
                             "sheet space" % (name, parts[index]["id"], x, y, direction, "; ".join(why)))
    return fails


def bed_failures(name: str, plan) -> list[str]:
    """The One bed rule on a whole Sheet's plan geometry (shapely)."""

    lo_x, lo_y, hi_x, hi_y = plan.bounds
    width, depth = hi_x - lo_x, hi_y - lo_y
    if max(width, depth) <= SHEET_MAX_MM + 1e-6:
        return []
    return ["%s: the Sheet is %.1f x %.1f mm in plan; it must fit %.0f x %.0f mm, the %.0f mm bed less %.0f mm "
            "a side: split it into two Sheets or move Parts to another"
            % (name, width, depth, SHEET_MAX_MM, SHEET_MAX_MM, BED_MM, BED_MARGIN_MM)]


def part_failures(sheets: list, printed: dict, totals: dict, measures: dict) -> tuple[list[str], list[str]]:
    """``(failures, small)`` over every printed Part of a kit with Sheets.

    ``printed`` maps each printed Part id to its tree entry (``small_reason``
    read there), ``totals`` to its count per toy, ``measures`` to its
    ``print_parts()`` measures (``size`` sorted, ``volume``). ``small`` lists
    the Parts that pass under R1 by their ``small_reason``."""

    on_sheets = {}
    for sheet in sheets:
        for entry in sheet["parts"]:
            on_sheets[entry["id"]] = on_sheets.get(entry["id"], 0) + entry["count"]
    fails, small = [], []
    for part in sorted(printed):
        measure = measures.get(part)
        if not measure:
            fails.append("%s: print_parts() did not measure it" % part)
            continue
        thick, short, long_ = measure["size"]
        under = [what for what, ok in (
            ("thickness %.1f < %.1f" % (thick, MIN_THICK), thick >= MIN_THICK - 1e-6),
            ("short side %.1f < %.1f" % (short, MIN_SHORT), short >= MIN_SHORT - 1e-6),
            ("long side %.1f < %.1f" % (long_, MIN_LONG), long_ >= MIN_LONG - 1e-6),
            ("footprint %.0f < %.0f mm2" % (short * long_, MIN_FOOT), short * long_ >= MIN_FOOT - 1e-6),
            ("volume %.0f < %.0f mm3" % (measure["volume"], MIN_VOLUME), measure["volume"] >= MIN_VOLUME - 1e-6),
        ) if not ok]
        if under and printed[part].get("small_reason"):
            small.append(part)
        elif under:
            fails.append("%s is under the minimum loose-part size (%s): merge, enlarge or carry it, or state its "
                         "small_reason" % (part, "; ".join(under)))
        if long_ < SPARE_BELOW_MM and part in on_sheets and on_sheets[part] < totals.get(part, 0) + 1:
            fails.append("%s is %.1f mm long, under %.0f: its Sheets carry %d, the toy uses %d; add one spare"
                         % (part, long_, SPARE_BELOW_MM, on_sheets[part], totals.get(part, 0)))
    return fails, small


# ---------------------------------------------------------------------------
# check: every Sheet of an installed kit tree

REPORT = "kit-sheets-report"


def _kit_tree():
    spec = importlib.util.spec_from_file_location("kit_sheets_kit_tree", Path(__file__).with_name("kit_tree.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def print_measures(project: Path, plan) -> tuple[dict, list[str]]:
    """``({Part id: {volume, area, size}}, failures)`` from each kit
    Component's ``print_parts()``, the shapes the Sheets must carry."""

    shapes, fails = print_shapes(project, plan)
    return {part: _measures(shape) for part, shape in shapes.items()}, fails


def print_shapes(project: Path, plan) -> tuple[dict, list[str]]:
    """``({Part id: shape}, failures)``: each printed Part's ``print_parts()``
    shape, in its print stance."""

    _runtime_paths()
    from printlib import detail_build, load_entry, project_on_path

    measures, fails = {}, []
    for role in sorted(plan.component_parts):
        wanted = [part for part in plan.component_parts[role] if part in plan.printed]
        if not wanted:
            continue
        entry = Path(project) / ("part_%s.step.py" % role)
        try:
            with project_on_path(entry.parent), contextlib.redirect_stdout(io.StringIO()), detail_build():
                built = load_entry(entry, "kit_sheets_parts").print_parts()
        except Exception as error:  # noqa: BLE001 - reported as a failure line
            fails.append("%s: print_parts() failed: %s: %s" % (entry.name, type(error).__name__, str(error)[:200]))
            continue
        for part in wanted:
            if part in built:
                measures[part] = built[part]
    return measures, fails


def check_project(project: Path, kit: dict | None = None) -> dict:
    """Every Sheet of the kit tree (``kit``, else the installed one) against
    its contract entry, and every printed Part against the size and spare
    rules."""

    project = Path(project)
    tree_tool = _kit_tree()
    if kit is None:
        kit = tree_tool.read_install(project)
    if not isinstance(kit, dict):
        return {"kind": REPORT, "verdict": "FAIL", "sheets": [], "small": [],
                "failures": ["the Assembly Tree is not installed (tree/kit.json)"]}
    sheets = (kit.get("assembly_tree") or {}).get("sheets") or []
    if not sheets:
        return {"kind": REPORT, "verdict": "PASS", "sheets": [], "small": [], "failures": []}
    plan = tree_tool.Plan(kit)
    fails = []
    declared = {"sheet_%s.py" % sheet["id"] for sheet in sheets}
    for stray in sorted(path.name for path in project.glob("sheet_*.py") if path.name not in declared):
        fails.append("%s is no Sheet of the contract: remove it" % stray)
    measures, measure_fails = print_measures(project, plan)
    fails += measure_fails
    for sheet in sheets:
        entry = project / ("sheet_%s.py" % sheet["id"])
        if not entry.is_file():
            fails.append("%s is missing: write Sheet %s (%s)" % (entry.name, sheet["id"], RULE))
            continue
        try:
            described = describe(entry)
        except Exception as error:  # noqa: BLE001 - reported as a failure line
            described = {"kind": KIND, "error": "sheet() failed: %s: %s" % (type(error).__name__, str(error)[:300])}
        fails += check(described, sheet, measures)
    printed = {part: plan.parts[part] for part in plan.printed}
    size_fails, small = part_failures(sheets, printed, plan.totals, measures)
    fails += size_fails
    return {"kind": REPORT, "verdict": "FAIL" if fails else "PASS", "sheets": [s["id"] for s in sheets],
            "small": small, "failures": fails}


def parse_report(stdout: str, returncode: int) -> dict:
    """A ``check`` run's report from its JSON line."""

    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                payload = json.loads(line)
            except ValueError:
                break
            if isinstance(payload, dict) and payload.get("kind") == REPORT:
                return payload
            break
    return {"kind": REPORT, "verdict": "FAIL", "sheets": [], "small": [],
            "failures": ["kit_sheets check exit %d produced no report" % returncode]}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) in (2, 4) and args[0] == "check" and (len(args) == 2 or args[2] == "--kit"):
        try:
            kit = json.loads(Path(args[3]).read_text(encoding="utf-8")) if len(args) == 4 else None
            report = check_project(Path(args[1]).resolve(), kit)
        except Exception as error:  # noqa: BLE001 - the CLI boundary
            report = {"kind": REPORT, "verdict": "FAIL", "sheets": [], "small": [],
                      "failures": ["kit_sheets check failed: %s: %s" % (type(error).__name__, str(error)[:300])]}
        for line in report["failures"]:
            print("FAIL %s" % line)
        if report["small"]:
            print("small Parts passed by small_reason: %s" % ", ".join(report["small"]))
        print(json.dumps(report, sort_keys=True))
        return 0 if report["verdict"] == "PASS" else 1
    if len(args) != 2 or args[0] != "describe" or not Path(args[1]).name.startswith("sheet_") or not args[1].endswith(".py"):
        print("usage: kit_sheets.py describe <project>/sheet_<id>.py | check <project> [--kit KIT.json]",
              file=sys.stderr)
        return 2
    entry = Path(args[1]).resolve()
    if not entry.is_file():
        print("kit_sheets.py: no such entry: %s" % entry, file=sys.stderr)
        return 2
    try:
        result = describe(entry)
    except Exception as error:  # noqa: BLE001 - the CLI boundary: report, do not traceback
        result = {"kind": KIND, "error": "sheet() failed: %s: %s" % (type(error).__name__, str(error)[:300])}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
