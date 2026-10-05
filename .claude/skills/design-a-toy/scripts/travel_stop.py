#!/usr/bin/env python3
"""Travel-stop placement check for design-a-toy Stage 3d.

    python3 travel_stop.py CHECK.json [--map]

One check is one travel stop the contract names: a hard stop that a host
Component's material puts at one extreme of a coupled motion ("hard stops on
vertical housing faces end both extremes"). Such a stop exists only if the
host can hold material that

1. lies outside every moving part's swept area over its travel, grown by the
   clearance;
2. lies in the way of a moving part a little past the extreme: inside the
   area that part would sweep over `overtravel_deg` more travel (its lead);
3. prints in the host's print stance: it grows from the bed, or from host
   material declared printable (`anchors`), through free space, never
   leaning further than `overhang_deg` from the build direction, and stays
   at least `min_thickness` thick on the way.

The verdict is PASS when some stopping mover's lead holds such material.
FAIL means no stop can be built in this host at this extreme as the contract
stands: the contract must name another stop (another Component, a shoulder
in the gear train, or a detent) before it is sealed.

The movers must turn about one axis normal to the plane, and every slice is
a slab of constant section along that axis (the movers' layer). The check
reads numbers only; it never builds CAD or draws an image.

CHECK.json (millimetres; degrees counterclockwise from the plane's first
axis toward its second, so for the X-Z plane a turn of +a about +Y is -a here):

    {
      "stop": "open extreme: hard stops on vertical housing faces (R03)",
      "host": "spine-housing",
      "stance": "upside down on its top face (Z 208.7)",
      "plane": ["X", "Z"],
      "build": [0, -1],
      "slices": [
        {"name": "sector layer Y 11.3 to 17.6",
         "outline": [[x, z], ...],
         "keep_out": [{"circle": {"center": [0, 180.9], "radius": 9.75}}],
         "anchors": [{"polygon": [[x, z], ...]}],
         "movers": [
           {"name": "wing#1", "pivot": [16, 198.8], "travel": [-35, 0],
            "shapes": [{"polygon": [[x, z], ...]}, {"circle": {...}}]}
         ]}
      ],
      "overtravel_deg": 4, "clearance": 0.5, "min_thickness": 0.8,
      "overhang_deg": 45, "grid_mm": 0.5, "step_deg": 1
    }

- `build`: the in-plane direction the print grows, from the bed toward later
  layers ([0, -1] for a part printed upside down on its top). The bed is the
  outline's line nearest the build's start, or `bed` (a build coordinate,
  `point . build`) when given. `"normal"` means the build runs along the
  movers' axis: every free point then rises as a wall from the bed, which is
  only true if the layers between the bed and the slice hold host material
  there; `swept_ceiling.py` checks that.
- `outline`: the host's section in this slice, as the contract allows it.
- `keep_out`: space the host may not fill for other reasons (another part's
  envelope, an opening the contract names).
- `anchors`: host material in the slice the contract already makes printable
  by other means (a pillar whose roof leans on a wall behind the slice).
  New material may grow from it. Leave it out unless the contract says so.
- `movers`: shapes in the pose where the mover's angle is 0, turned about
  `pivot`. `travel` is [from, to]: the mover goes from `from` to `to`, `to` is
  the extreme this stop ends, and the overtravel continues past `to`. Every
  mover in the slice blocks its swept area. A mover with `"stops": false`
  blocks space but its lead does not count (a part not coupled to the
  motion).

Sampling: the step is at most `step_deg` and at most clearance / (the
farthest outline point from the pivot), in radians, so the sampled sweep
covers the true sweep grown by at least half the clearance; a lead point
counts when a sampled overtravel pose comes within half a step's arc of it.

Report, per slice and stopping mover: lead points inside the outline and
free, lead points outside the outline, the stop site (lead points that are
printable material) with its area and box, and the gap from the free lead to
the nearest printable material.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from swept_ceiling import _inside, _rotate, _shape_distance  # noqa: E402

Point = tuple[float, float]

OUTSIDE, BLOCKED, FREE = 0, 1, 2


def _normalise(vector: list[float]) -> Point:
    length = math.hypot(vector[0], vector[1])
    if length == 0:
        raise ValueError("build direction is zero")
    return (vector[0] / length, vector[1] / length)


def _radius(shape: dict, pivot: Point) -> float:
    if "circle" in shape:
        cx, cy = shape["circle"]["center"]
        return math.hypot(cx - pivot[0], cy - pivot[1]) + shape["circle"]["radius"]
    return max(math.hypot(x - pivot[0], y - pivot[1]) for x, y in shape["polygon"])


def _box(shape: dict) -> tuple[float, float, float, float]:
    if "circle" in shape:
        (cx, cy), r = shape["circle"]["center"], shape["circle"]["radius"]
        return (cx - r, cy - r, cx + r, cy + r)
    xs = [p[0] for p in shape["polygon"]]
    ys = [p[1] for p in shape["polygon"]]
    return (min(xs), min(ys), max(xs), max(ys))


def _near(point: Point, shapes: list[tuple[dict, tuple]], within: float) -> bool:
    x, y = point
    for shape, (x0, y0, x1, y1) in shapes:
        if x < x0 - within or x > x1 + within or y < y0 - within or y > y1 + within:
            continue
        if _shape_distance(point, shape) <= within:
            return True
    return False


def _sweep_angles(start: float, end: float, step: float) -> list[float]:
    count = max(1, math.ceil(abs(end - start) / step - 1e-9))
    return [start + (end - start) * i / count for i in range(count + 1)]


class _Mover:
    def __init__(self, mover: dict, step: float, overtravel: float, reach: float, clearance: float):
        self.name = mover["name"]
        self.stops = bool(mover.get("stops", True))
        self.pivot = tuple(mover["pivot"])
        self.shapes = [(shape, _box(shape)) for shape in mover["shapes"]]
        start, end = (float(a) for a in mover["travel"])
        self.radius = max(_radius(shape, self.pivot) for shape in mover["shapes"])
        # Fine enough that a point at the farthest outline reach moves at
        # most the clearance between samples.
        self.step = min(step, math.degrees(clearance / max(reach, 1e-9))) if clearance > 0 else step
        self.travel = _sweep_angles(start, end, self.step)
        sign = 1.0 if end >= start else -1.0
        beyond = end + sign * overtravel
        self.lead = _sweep_angles(end, beyond, self.step)[1:] if overtravel > 0 else []

    def _covers(self, point: Point, angles: list[float], within: float) -> bool:
        if math.hypot(point[0] - self.pivot[0], point[1] - self.pivot[1]) > self.radius + within:
            return False
        for angle in angles:
            # The mover turned by `angle` covers the point exactly when the
            # point turned back by `angle` lies on the mover's 0 pose.
            if _near(_rotate(point, self.pivot, -angle), self.shapes, within):
                return True
        return False

    def sweeps(self, point: Point, clearance: float) -> bool:
        return self._covers(point, self.travel, clearance)

    def leads(self, point: Point) -> bool:
        distance = math.hypot(point[0] - self.pivot[0], point[1] - self.pivot[1])
        tolerance = distance * math.radians(self.step) / 2
        return self._covers(point, self.lead, tolerance)


def _check_slice(check: dict, piece: dict) -> dict:
    grid = float(check.get("grid_mm", 0.5))
    clearance = float(check.get("clearance", 0.5))
    overtravel = float(check.get("overtravel_deg", 4.0))
    thickness = float(check.get("min_thickness", 0.8))
    overhang = float(check.get("overhang_deg", 45.0))
    step = float(check.get("step_deg", 1.0))
    build = check.get("build", "normal")
    outline = [tuple(p) for p in piece["outline"]]
    keep_out = [(shape, _box(shape)) for shape in piece.get("keep_out", [])]
    anchors = [(shape, _box(shape)) for shape in piece.get("anchors", [])]

    if build == "normal":
        along, across, rows_pitch = (0.0, 1.0), (1.0, 0.0), grid
    else:
        along = _normalise(build)
        across = (-along[1], along[0])
        # One cell sideways per row is exactly the overhang limit.
        rows_pitch = grid / math.tan(math.radians(overhang))

    def to_plane(u: float, v: float) -> Point:
        return (u * across[0] + v * along[0], u * across[1] + v * along[1])

    us = [p[0] * across[0] + p[1] * across[1] for p in outline]
    vs = [p[0] * along[0] + p[1] * along[1] for p in outline]
    u0 = min(us)
    v0 = float(check["bed"]) if build != "normal" and "bed" in check else min(vs)
    # Cell centres, so the first row sits half a row inside the bed.
    columns = max(1, math.ceil((max(us) - u0) / grid))
    rows = max(1, math.ceil((max(vs) - v0) / rows_pitch))

    reach = 0.0
    for mover in piece["movers"]:
        reach = max(reach, max(math.hypot(x - mover["pivot"][0], y - mover["pivot"][1])
                               for x, y in outline))
    movers = [_Mover(m, step, overtravel, reach, clearance) for m in piece["movers"]]

    state = [[OUTSIDE] * columns for _ in range(rows)]
    anchored = [[False] * columns for _ in range(rows)]
    points: dict[tuple[int, int], Point] = {}
    for row in range(rows):
        for column in range(columns):
            point = to_plane(u0 + (column + 0.5) * grid, v0 + (row + 0.5) * rows_pitch)
            points[(row, column)] = point
            if not _inside(point, outline):
                continue
            if _near(point, keep_out, 0.0) or any(m.sweeps(point, clearance) for m in movers):
                state[row][column] = BLOCKED
                continue
            state[row][column] = FREE
            anchored[row][column] = _near(point, anchors, 0.0)

    # Thick enough to grow through: no blocked or outside point within half
    # the minimum thickness.
    half = thickness / 2
    reach_columns = int(math.ceil(half / grid))
    reach_rows = int(math.ceil(half / rows_pitch))
    offsets = [
        (dr, dc) for dr in range(-reach_rows, reach_rows + 1)
        for dc in range(-reach_columns, reach_columns + 1)
        if math.hypot(dr * rows_pitch, dc * grid) <= half + 1e-9
    ]

    def core(row: int, column: int) -> bool:
        for dr, dc in offsets:
            r, c = row + dr, column + dc
            if r < 0 and build != "normal":
                continue  # the bed
            if not (0 <= r < rows and 0 <= c < columns) or state[r][c] != FREE:
                return False
        return True

    printable = [[False] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            if state[row][column] != FREE:
                continue
            if anchored[row][column]:
                printable[row][column] = True
                continue
            if not core(row, column):
                continue
            if build == "normal" or row == 0:
                printable[row][column] = True
                continue
            printable[row][column] = any(
                0 <= column + dc < columns and printable[row - 1][column + dc]
                for dc in (-1, 0, 1)
            )
    # Material: the printable cores grown back by half the thickness, within
    # free space; anchors count as they are.
    material = [[False] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            if not printable[row][column]:
                continue
            for dr, dc in offsets if not anchored[row][column] else [(0, 0)]:
                r, c = row + dr, column + dc
                if 0 <= r < rows and 0 <= c < columns and state[r][c] == FREE:
                    material[r][c] = True

    cell_area = grid * rows_pitch
    material_points = [points[(r, c)] for r in range(rows) for c in range(columns) if material[r][c]]
    results = []
    for mover in movers:
        if not mover.stops:
            continue
        free_lead, outside_lead, site = [], 0, []
        for row in range(rows):
            for column in range(columns):
                cell = state[row][column]
                if cell == BLOCKED:
                    continue
                point = points[(row, column)]
                if not mover.leads(point):
                    continue
                if cell == OUTSIDE:
                    outside_lead += 1
                    continue
                free_lead.append(point)
                if material[row][column]:
                    site.append(point)
        # Lead points beyond the box of the outline are not sampled; count
        # the in-box ones as "outside" only.
        gap = None
        if free_lead and material_points:
            gap = min(
                math.hypot(p[0] - q[0], p[1] - q[1]) for p in free_lead for q in material_points
            )
        result = {
            "mover": mover.name,
            "step_deg": round(mover.step, 4),
            "lead_free_mm2": round(len(free_lead) * cell_area, 3),
            "lead_outside_outline_mm2": round(outside_lead * cell_area, 3),
            "site_mm2": round(len(site) * cell_area, 3),
            "gap_to_printable_mm": None if gap is None else round(gap, 2),
        }
        if site:
            xs = [p[0] for p in site]
            ys = [p[1] for p in site]
            result["site_box"] = [round(min(xs), 2), round(min(ys), 2),
                                  round(max(xs), 2), round(max(ys), 2)]
        results.append(result)

    return {
        "slice": piece.get("name"),
        "printable_mm2": round(len(material_points) * cell_area, 3),
        "movers": results,
        "_grid": (state, material, points, rows, columns),
    }


def run_check(check: dict) -> dict:
    slices = [_check_slice(check, piece) for piece in check["slices"]]
    sites = [
        (piece["slice"], mover["mover"], mover["site_mm2"])
        for piece in slices for mover in piece["movers"] if mover["site_mm2"] > 0
    ]
    problems = []
    if not sites:
        problems.append(
            f"no printable {check.get('host', 'host')} material lies in any stopping mover's "
            f"lead {float(check.get('overtravel_deg', 4.0)):g} degrees past this extreme: "
            "name another stop (another Component, the gear train or a detent)"
        )
    return {
        "stop": check.get("stop"),
        "host": check.get("host"),
        "stance": check.get("stance"),
        "verdict": "PASS" if sites else "FAIL",
        "problems": problems,
        "sites": [{"slice": s, "mover": m, "area_mm2": a} for s, m, a in sites],
        "slices": slices,
    }


def ascii_map(piece: dict, every: float = 1.0, grid: float = 0.5) -> str:
    """Rows in build order from the bed: `#` blocked, `.` free, `o` printable."""

    state, material, _points, rows, columns = piece["_grid"]
    stride = max(1, round(every / grid))
    lines = []
    for row in range(0, rows, stride):
        marks = "".join(
            "o" if material[row][c] else " #."[state[row][c]]
            for c in range(0, columns, stride)
        )
        lines.append(marks)
    return "\n".join(lines)


def printable_report(report: dict) -> dict:
    return {
        **{k: v for k, v in report.items() if k != "slices"},
        "slices": [{k: v for k, v in s.items() if not k.startswith("_")} for s in report["slices"]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("check", help="the check's JSON file")
    parser.add_argument("--map", action="store_true", help="also print each slice's map")
    args = parser.parse_args(argv)
    with open(args.check, encoding="utf-8") as handle:
        check = json.load(handle)
    report = run_check(check)
    print(json.dumps(printable_report(report), indent=2))
    if args.map:
        for piece in report["slices"]:
            print(f"slice {piece['slice']} (from the bed)")
            print(ascii_map(piece, grid=float(check.get("grid_mm", 0.5))))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
