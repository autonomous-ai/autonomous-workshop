#!/usr/bin/env python3
"""Camera-composition check for design-a-toy Stage 3d.

    python3 camera_composition.py CHECK.json

A requirement that names a camera and claims a composition in the Display
Pose ("framed by the open wings as a V", "the staff is level", "the shield is
in front of the chest") is true only if the landmarks the contract pins
project that way through that camera. This script projects them and judges
the claim from numbers; it never builds CAD or draws an image.

The camera is `[AZ, EL]` in degrees in `render_review`'s convention, the one
`references[].camera` uses (CONTRACT-FORMAT.md): the camera looks from
direction (cos EL cos AZ, cos EL sin AZ, sin EL) toward the toy, so AZ 0
looks from +X (the figure's left), -90 from the front (-Y), 90 from the back
and 180 from -X (the figure's right); EL 0 is level and 90 looks straight
down. The projection is orthographic, as Make's renders are. Screen x grows
to the image's right, screen y up, and depth toward the viewer (a larger
depth is nearer).

Prose that gives a camera in some other convention ("35 degrees azimuth",
measured from the front) is converted to this one first, and the conversion
written in the working notes; check both readings when the prose is
ambiguous, and fix the words if they disagree.

CHECK.json (millimetres, Display Pose / assembly frame):

    {
      "cameras": {"R01": [35, 22], "ref-01": [-90, 15]},
      "points": {"hinge-left": [16, 17.5, 198.8], "heart": [0, -12, 180.9]},
      "segments": [
        {"name": "wing#1 top blade", "from": "hinge-left",
         "along": [0.99719, 0, 0.07498], "length": 175},
        {"name": "wing#2 top blade", "from": [-16, 17.5, 198.8],
         "to": [-190.5, 17.5, 211.9]}
      ],
      "claims": [
        {"name": "R01 wings as a V", "kind": "v",
         "segments": ["wing#1 top blade", "wing#2 top blade"],
         "cameras": ["R01"], "min_rise_deg": 2, "symmetry_deg": 5},
        {"name": "blades read as one line", "kind": "line",
         "segments": ["wing#1 top blade", "wing#2 top blade"],
         "tolerance_deg": 5},
        {"name": "heart in front of the hinge", "kind": "in_front",
         "near": "heart", "far": "hinge-left"}
      ]
    }

A point is a name from `points` or an `[x, y, z]` list. A segment runs
`from` its inner end (the hinge, root or pivot) `to` its outer end, or
`along` a direction for `length`. A claim with no `cameras` is judged from
every camera.

Each segment is reported per camera with its projected ends, its screen
angle (counterclockwise from screen right, -180..180) and its rise: the
outward end's angle above screen horizontal, whichever side it points to.

Claims:

- `v`: two segments point to opposite screen sides, each rises at least
  `min_rise_deg` (default 2), and their rises differ by at most
  `symmetry_deg` (default 5). A mirrored pair from a camera off the mirror
  plane rises unevenly; one that falls is not a V.
- `line`: two segments point to opposite screen sides and read as one
  straight line: their screen directions are within `tolerance_deg`
  (default 5) of opposite.
- `in_front`: `near` is nearer the camera than `far` by at least
  `margin_mm` (default 0).

The verdict is PASS only when every claim holds from every camera it names;
the exit code is 1 otherwise. Claims the script cannot judge (framing,
arcs, silhouette) are judged by eye from the printed screen positions.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

Vector = tuple[float, float, float]


def camera_basis(azimuth: float, elevation: float) -> tuple[Vector, Vector, Vector]:
    """Toward-viewer, screen-right and screen-up unit vectors.

    Mirrors `camera_basis` in src/workshop/make/skills/cad/scripts/render_review.
    """
    az = math.radians(azimuth)
    el = math.radians(elevation)
    toward = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    right = (-toward[1], toward[0], 0.0)  # +Z x toward
    length = math.hypot(right[0], right[1])
    if length < 1e-9:
        right = (-math.sin(az), math.cos(az), 0.0)
    else:
        right = (right[0] / length, right[1] / length, 0.0)
    up = (
        toward[1] * right[2] - toward[2] * right[1],
        toward[2] * right[0] - toward[0] * right[2],
        toward[0] * right[1] - toward[1] * right[0],
    )
    return toward, right, up


def _dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def project(point: Vector, camera: list[float]) -> dict:
    toward, right, up = camera_basis(float(camera[0]), float(camera[1]))
    return {"x": _dot(point, right), "y": _dot(point, up), "depth": _dot(point, toward)}


def _point(value, points: dict) -> Vector:
    if isinstance(value, str):
        if value not in points:
            raise ValueError(f"unknown point {value!r}")
        value = points[value]
    if len(value) != 3:
        raise ValueError(f"a point is [x, y, z], not {value!r}")
    return tuple(float(v) for v in value)


def _segment_ends(segment: dict, points: dict) -> tuple[Vector, Vector]:
    start = _point(segment["from"], points)
    if "to" in segment:
        return start, _point(segment["to"], points)
    along = _point(segment["along"], {})
    norm = math.sqrt(_dot(along, along))
    if norm < 1e-12:
        raise ValueError(f"segment {segment.get('name')!r} has a zero direction")
    length = float(segment["length"])
    return start, tuple(s + a / norm * length for s, a in zip(start, along))


def screen_segment(start: Vector, end: Vector, camera: list[float]) -> dict:
    a, b = project(start, camera), project(end, camera)
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    return {
        "from": [round(a["x"], 2), round(a["y"], 2)],
        "to": [round(b["x"], 2), round(b["y"], 2)],
        "screen_length": round(math.hypot(dx, dy), 2),
        "angle_deg": round(math.degrees(math.atan2(dy, dx)), 2),
        "rise_deg": round(math.degrees(math.atan2(dy, abs(dx))), 2),
        "side": "right" if dx > 0 else "left" if dx < 0 else "none",
    }


def _judge(claim: dict, camera: list[float], segments: dict, points: dict) -> tuple[bool, str]:
    kind = claim["kind"]
    if kind in ("v", "line"):
        first, second = (screen_segment(*segments[name], camera) for name in claim["segments"])
        opposite = {first["side"], second["side"]} == {"left", "right"}
        if kind == "v":
            low = float(claim.get("min_rise_deg", 2))
            spread = float(claim.get("symmetry_deg", 5))
            rises = (first["rise_deg"], second["rise_deg"])
            difference = abs(rises[0] - rises[1])
            held = opposite and min(rises) >= low and difference <= spread
            return held, (f"rises {rises[0]:.1f} and {rises[1]:.1f} deg, differ {difference:.1f}"
                          f" (V needs opposite sides, each >= {low:g}, differ <= {spread:g})"
                          + ("" if opposite else "; both on one side"))
        tolerance = float(claim.get("tolerance_deg", 5))
        bend = abs(((first["angle_deg"] - second["angle_deg"]) % 360) - 180)
        held = opposite and bend <= tolerance
        return held, f"bend {bend:.1f} deg from straight (line needs <= {tolerance:g})"
    if kind == "in_front":
        near = project(_point(claim["near"], points), camera)["depth"]
        far = project(_point(claim["far"], points), camera)["depth"]
        margin = float(claim.get("margin_mm", 0))
        return near - far >= margin, f"near is {near - far:.1f} mm nearer (needs >= {margin:g})"
    raise ValueError(f"unknown claim kind {kind!r}")


def run_check(check: dict) -> dict:
    cameras = check.get("cameras") or {"camera": check["camera"]}
    points = check.get("points", {})
    segments = {seg["name"]: _segment_ends(seg, points) for seg in check.get("segments", [])}
    report = {"cameras": {}, "claims": [], "verdict": "PASS"}
    for label, camera in cameras.items():
        report["cameras"][label] = {
            "camera": list(camera),
            "segments": {name: screen_segment(*ends, camera) for name, ends in segments.items()},
            "points": {name: {k: round(v, 2) for k, v in project(_point(p, {}), camera).items()}
                       for name, p in points.items()},
        }
    for claim in check.get("claims", []):
        for label in claim.get("cameras", list(cameras)):
            held, detail = _judge(claim, cameras[label], segments, points)
            report["claims"].append({"name": claim.get("name", claim["kind"]), "camera": label,
                                     "verdict": "PASS" if held else "FAIL", "detail": detail})
            if not held:
                report["verdict"] = "FAIL"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("check", help="CHECK.json")
    args = parser.parse_args(argv)
    with open(args.check, encoding="utf-8") as handle:
        report = run_check(json.load(handle))
    for label, view in report["cameras"].items():
        az, el = view["camera"]
        print(f"camera {label} [{az:g}, {el:g}]")
        for name, seg in view["segments"].items():
            print(f"  {name}: {seg['from']} -> {seg['to']}, angle {seg['angle_deg']:.1f},"
                  f" rise {seg['rise_deg']:.1f} toward screen {seg['side']}")
        for name, pt in view["points"].items():
            print(f"  {name}: x {pt['x']:.1f}, y {pt['y']:.1f}, depth {pt['depth']:.1f}")
    for claim in report["claims"]:
        print(f"{claim['verdict']} {claim['name']} from {claim['camera']}: {claim['detail']}")
    print(f"verdict {report['verdict']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
