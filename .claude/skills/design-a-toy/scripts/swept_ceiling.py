#!/usr/bin/env python3
"""Swept-volume-over-ceiling check for design-a-toy Stage 3c.

    python3 swept_ceiling.py CHECK.json [--map]

One check is one printed part in its print stance, seen along the build
direction, and the moving parts whose travel passes under one of its ceilings.
The movers must turn about axes along the build direction, so each sweeps a
layer parallel to the bed; for any other mechanism, sample the sweep by hand.
Every coordinate is in the plane parallel to the bed, in the contract's
assembly frame (for a part printed on a face normal to Y, the X-Z plane).
Angles are degrees, counterclockwise from the plane's first axis toward its
second.

A mover's swept area (its shapes at every step of its travel, grown by the
clearance) is space the part may not fill, from the bed to the ceiling, so
nothing of the part can stand under the ceiling there. Every other point
inside the part's outline is a possible support. A ceiling point over the
swept area prints only as:

- a bridge: support on both sides of it, along one line, within `bridge_mm`;
- or a vault: the ceiling rises from the nearest support at `overhang_deg`
  from horizontal, so at distance d it stands `tan(overhang_deg) * d` above
  its base, and that must stay at or under `max_height`.

The base is the declared ceiling, which must itself clear every mover's top
by the clearance. Each named seat (a hinge or axle seat in the ceiling) must
print one of the two ways, with the vault judged against its own
`max_height`, the highest it may sit and still hold its pin.

CHECK.json:

    {
      "part": "spine-housing",
      "stance": "front face on the bed (Y 7.3), building toward +Y",
      "plane": ["X", "Z"],
      "outline": [[x, z], ...],
      "ceiling": {"height": 17.5, "max_height": 34.6},
      "movers": [
        {"name": "wing#1", "pivot": [16, 198.8], "start_deg": 0, "end_deg": 35,
         "top": 17.1,
         "shapes": [{"circle": {"center": [16, 198.8], "radius": 17.1}},
                    {"polygon": [[x, z], ...]}],
         "keep_below": 206.2}
      ],
      "seats": [{"name": "wing#1 hinge seat", "at": [16, 198.8], "max_height": 17.5}],
      "clearance": 0.5, "bridge_mm": 12, "overhang_deg": 50,
      "grid_mm": 0.5, "step_deg": 2.5
    }

Shapes are given in the mover's start pose, in plane coordinates. An optional
`keep_below` on a mover trims it: inside the outline it never reaches above
that height (the second plane axis), whatever its pose. That models a
proposed amendment ("the wing stays below Z 206.2 inside the housing"); the
teeth or plate it trims away are the amendment's own cost, which Stage 3d
re-checks.

The verdict is PASS only when the ceiling clears every mover and every
swept point and seat prints. The script reads numbers; it never builds CAD
or draws an image.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Iterable

Point = tuple[float, float]

DIRECTIONS = 32


def _inside(point: Point, polygon: list[Point]) -> bool:
    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < crossing:
                inside = not inside
    return inside


def _segment_distance(point: Point, a: Point, b: Point) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _shape_distance(point: Point, shape: dict) -> float:
    """Distance from a point to a shape; 0 inside it."""

    if "circle" in shape:
        cx, cy = shape["circle"]["center"]
        return max(0.0, math.hypot(point[0] - cx, point[1] - cy) - shape["circle"]["radius"])
    polygon = [tuple(p) for p in shape["polygon"]]
    if _inside(point, polygon):
        return 0.0
    return min(
        _segment_distance(point, polygon[i], polygon[(i + 1) % len(polygon)])
        for i in range(len(polygon))
    )


def _rotate(point: Point, pivot: Point, degrees: float) -> Point:
    angle = math.radians(degrees)
    x, y = point[0] - pivot[0], point[1] - pivot[1]
    return (
        pivot[0] + x * math.cos(angle) - y * math.sin(angle),
        pivot[1] + x * math.sin(angle) + y * math.cos(angle),
    )


def _angles(mover: dict, step: float) -> list[float]:
    start, end = float(mover["start_deg"]), float(mover["end_deg"])
    count = max(1, math.ceil(abs(end - start) / step))
    return [start + (end - start) * i / count for i in range(count + 1)]


def _swept_by(point: Point, mover: dict, angles: Iterable[float], clearance: float) -> bool:
    keep_below = mover.get("keep_below")
    if keep_below is not None and point[1] > keep_below + clearance:
        return False
    pivot = tuple(mover["pivot"])
    for angle in angles:
        # The mover turned by `angle` covers the point exactly when the
        # point turned back by `angle` lies on the mover's start pose.
        local = _rotate(point, pivot, -angle)
        if any(_shape_distance(local, shape) <= clearance for shape in mover["shapes"]):
            return True
    return False


def run_check(check: dict) -> dict:
    outline = [tuple(p) for p in check["outline"]]
    clearance = float(check.get("clearance", 0.5))
    bridge = float(check.get("bridge_mm", 12.0))
    rise = math.tan(math.radians(float(check.get("overhang_deg", 50.0))))
    grid = float(check.get("grid_mm", 0.5))
    step = float(check.get("step_deg", 2.5))
    ceiling = check["ceiling"]
    base = float(ceiling["height"])
    max_height = float(ceiling["max_height"])
    movers = check["movers"]
    problems: list[str] = []

    for mover in movers:
        needed = float(mover["top"]) + clearance
        if base < needed - 1e-9:
            problems.append(
                f"ceiling {base:g} is inside {mover['name']}'s clearance: "
                f"its top {float(mover['top']):g} + {clearance:g} needs {needed:g}"
            )
    vault_base = max([base] + [float(m["top"]) + clearance for m in movers])

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    x0, y0 = min(xs), min(ys)
    columns = int(math.floor((max(xs) - x0) / grid)) + 1
    rows = int(math.floor((max(ys) - y0) / grid)) + 1
    angles = {m["name"]: _angles(m, step) for m in movers}
    # 0 outside the outline, 1 support, 2 swept.
    cells = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            point = (x0 + column * grid, y0 + row * grid)
            if not _inside(point, outline):
                continue
            swept = any(_swept_by(point, m, angles[m["name"]], clearance) for m in movers)
            cells[row][column] = 2 if swept else 1

    def ray(row: int, column: int, dx: float, dy: float) -> float:
        distance = 0.0
        while True:
            distance += grid
            r = round(row + dy * distance / grid)
            c = round(column + dx * distance / grid)
            if not (0 <= r < rows and 0 <= c < columns) or cells[r][c] == 0:
                return math.inf
            if cells[r][c] == 1:
                return distance

    directions = [
        (math.cos(2 * math.pi * k / DIRECTIONS), math.sin(2 * math.pi * k / DIRECTIONS))
        for k in range(DIRECTIONS)
    ]

    def judge(row: int, column: int) -> tuple[float, float, float]:
        lengths = [ray(row, column, dx, dy) for dx, dy in directions]
        half = DIRECTIONS // 2
        span = min(lengths[k] + lengths[k + half] for k in range(half))
        nearest = min(lengths)
        return span, nearest, vault_base + rise * nearest

    swept = unsupported = 0
    worst: tuple[float, Point] | None = None
    unsupported_box: list[float] | None = None
    for row in range(rows):
        for column in range(columns):
            if cells[row][column] != 2:
                continue
            swept += 1
            span, nearest, height = judge(row, column)
            if span <= bridge or height <= max_height:
                continue
            unsupported += 1
            point = (round(x0 + column * grid, 3), round(y0 + row * grid, 3))
            if worst is None or height > worst[0]:
                worst = (height, point)
            if unsupported_box is None:
                unsupported_box = [point[0], point[1], point[0], point[1]]
            else:
                unsupported_box = [
                    min(unsupported_box[0], point[0]), min(unsupported_box[1], point[1]),
                    max(unsupported_box[2], point[0]), max(unsupported_box[3], point[1]),
                ]
    if unsupported:
        problems.append(
            f"{unsupported} of {swept} swept ceiling points neither bridge within {bridge:g} "
            f"nor vault under {max_height:g}"
        )

    seats = []
    for seat in check.get("seats", []):
        sx, sy = seat["at"]
        column = round((sx - x0) / grid)
        row = round((sy - y0) / grid)
        inside = 0 <= row < rows and 0 <= column < columns
        state = cells[row][column] if inside else 0
        if state == 1:
            result = {"name": seat["name"], "swept": False, "verdict": "PASS"}
        elif state == 0:
            result = {"name": seat["name"], "swept": False, "verdict": "FAIL",
                      "why": "outside the part's outline"}
        else:
            span, nearest, height = judge(row, column)
            limit = float(seat.get("max_height", max_height))
            ok = span <= bridge or height <= limit
            result = {
                "name": seat["name"], "swept": True,
                "bridge_span": None if math.isinf(span) else round(span, 2),
                "nearest_support": None if math.isinf(nearest) else round(nearest, 2),
                "vault_height": None if math.isinf(height) else round(height, 2),
                "max_height": limit,
                "verdict": "PASS" if ok else "FAIL",
            }
            if not ok:
                span_text = "none" if result["bridge_span"] is None else f"{result['bridge_span']:g}"
                problems.append(
                    f"seat {seat['name']}: bridge span {span_text} > {bridge:g} "
                    f"and vault height {result['vault_height']} > {limit:g}"
                )
        seats.append(result)

    report = {
        "part": check.get("part"),
        "stance": check.get("stance"),
        "verdict": "FAIL" if problems else "PASS",
        "problems": problems,
        "vault_base": vault_base,
        "swept_points": swept,
        "unsupported_points": unsupported,
        "unsupported_box": unsupported_box,
        "worst_vault": None if worst is None else {
            "at": list(worst[1]),
            "height": None if math.isinf(worst[0]) else round(worst[0], 2),
        },
        "seats": seats,
    }
    report["_cells"] = (cells, x0, y0, grid)
    return report


def ascii_map(report: dict, every: float = 1.0) -> str:
    """Rows from the top: `#` swept, `.` possible support, blank outside."""

    cells, x0, y0, grid = report["_cells"]
    stride = max(1, round(every / grid))
    lines = []
    for row in range(len(cells) - 1, -1, -stride):
        marks = "".join(" .#"[cells[row][c]] for c in range(0, len(cells[0]), stride))
        lines.append(f"{y0 + row * grid:7.1f} {marks}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("check", help="the check's JSON file")
    parser.add_argument("--map", action="store_true", help="also print the swept map")
    args = parser.parse_args(argv)
    with open(args.check, encoding="utf-8") as handle:
        report = run_check(json.load(handle))
    printable = {k: v for k, v in report.items() if not k.startswith("_")}
    print(json.dumps(printable, indent=2))
    if args.map:
        print(ascii_map(report))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
