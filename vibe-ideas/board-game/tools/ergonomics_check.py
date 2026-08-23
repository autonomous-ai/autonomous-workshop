#!/usr/bin/env python3
"""ergonomics_check.py — gate R2. Arithmetic on the brief's millimetres.

    python3 board-game/tools/ergonomics_check.py board-game/ideas/<slug>/brief.json

Sits between the brief and the build: the first moment real dimensions exist,
and the last moment before geometry costs anything. Everything here is a
subtraction, but each one stands for a game that is unplayable in the hand
while being flawless on every geometric measure — which is exactly the gap
that "in được + chơi được" is meant to close and that a printability score
alone will never see.

The one that motivated the file: turn 15's Sluice Row seated 7mm seed-weights
on the floor of 26mm-wide, 16mm-deep wells — 9mm below the rim, with 3mm of
room around them. Every geometric check passed. Try getting one out with your
fingers.

The brief carries a machine-readable block; `bbox_mm` is [x, y, z] with z the
height as the piece sits on the table:

    {
      "parts": [
        {"name": "seed_small", "kind": "loose_piece", "bbox_mm": [20, 20, 7]},
        {"name": "trough_board", "kind": "board", "bbox_mm": [240, 120, 16],
         "recesses": [{"holds": "seed_small", "width_mm": 26, "depth_mm": 16,
                       "count": 12}],
         "relief_mm": 0.5}
      ]
    }

Exit 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Thresholds — code tier, PR only. Each is a hand, not a preference.
# ---------------------------------------------------------------------------

# Below this an adult fumbles the piece off the table. Measured on the two
# smallest dimensions, because a long thin sliver is not graspable either.
MIN_GRASP_MM = 8.0

# To lift a piece out of a recess you need one of two things: something to
# pinch above the rim, or room beside it for a fingertip.
MIN_PROTRUSION_MM = 2.0
FINGER_ROOM_MM = 12.0

# A piece must drop into its seat, not be pressed into it. Board game pieces
# are handled hundreds of times; a press fit becomes damage.
MIN_SEAT_CLEARANCE_MM = 0.4

# Tall and narrow falls over every time someone nudges the table.
MAX_STACK_ASPECT = 3.0

# Graduated from CAD_GRAMMAR: sub-millimetre relief was repeatedly modelled
# faithfully and then invisible in the printed object and in every render.
MIN_RELIEF_MM = 0.6


def _base_and_height(bbox: list) -> tuple[float, float, float]:
    x, y, z = (float(v) for v in bbox)
    return x, y, z


def check(brief: dict) -> list:
    findings: list[str] = []
    parts = brief.get("parts") or []
    if not parts:
        return ["brief: no parts block — nothing to measure"]

    by_name = {}
    for part in parts:
        name = str(part.get("name", "")).strip()
        bbox = part.get("bbox_mm")
        if not name or not bbox or len(bbox) != 3:
            findings.append(f"brief:{name or '?'}: needs a name and bbox_mm [x, y, z]")
            continue
        by_name[name] = part

    for name, part in by_name.items():
        x, y, z = _base_and_height(part["bbox_mm"])
        kind = str(part.get("kind", "")).lower()

        if kind == "loose_piece":
            two_smallest = sorted((x, y, z))[:2]
            if two_smallest[1] < MIN_GRASP_MM:
                findings.append(
                    f"grasp:{name}: {x}x{y}x{z}mm — its two smallest dimensions are "
                    f"{two_smallest[0]}mm and {two_smallest[1]}mm, under the "
                    f"{MIN_GRASP_MM}mm a hand needs to pick it up reliably")
            if part.get("stackable") and z / max(min(x, y), 0.1) > MAX_STACK_ASPECT:
                findings.append(
                    f"stack:{name}: {z}mm tall on a {min(x, y)}mm base is over "
                    f"{MAX_STACK_ASPECT}:1 — it topples when the table is nudged")

        relief = part.get("relief_mm")
        if relief is not None and float(relief) < MIN_RELIEF_MM:
            findings.append(
                f"relief:{name}: {relief}mm of relief is under {MIN_RELIEF_MM}mm — "
                f"this class has repeatedly been modelled correctly and then been "
                f"invisible in the printed object")

        for i, recess in enumerate(part.get("recesses") or [], 1):
            holds = str(recess.get("holds", "")).strip()
            width = float(recess.get("width_mm", 0))
            depth = float(recess.get("depth_mm", 0))
            tag = f"{name}.recess[{i}]"
            if holds not in by_name:
                findings.append(f"seat:{tag}: holds '{holds}', which is not a part "
                                f"in this brief")
                continue
            px, py, pz = _base_and_height(by_name[holds]["bbox_mm"])
            footprint = max(px, py)

            clearance = (width - footprint) / 2.0
            if clearance < MIN_SEAT_CLEARANCE_MM:
                findings.append(
                    f"seat:{tag}: a {width}mm opening around a {footprint}mm piece "
                    f"leaves {clearance:.2f}mm per side, under the "
                    f"{MIN_SEAT_CLEARANCE_MM}mm needed to drop in rather than press in")

            protrusion = pz - depth
            if protrusion < MIN_PROTRUSION_MM and clearance < FINGER_ROOM_MM:
                findings.append(
                    f"retrieve:{tag}: a {pz}mm piece in a {depth}mm-deep pocket sits "
                    f"{-protrusion:.1f}mm below the rim with {clearance:.1f}mm beside "
                    f"it — nothing to pinch and no room for a fingertip. Make the "
                    f"pocket shallower than {pz - MIN_PROTRUSION_MM:.1f}mm, or widen "
                    f"it past {footprint + 2 * FINGER_ROOM_MM:.0f}mm, or cut a finger "
                    f"notch into the rim")

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("brief", type=Path)
    ap.add_argument("--out", type=Path, help="default <brief dir>/ergonomics_check.json")
    args = ap.parse_args()

    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    findings = check(brief)
    report = {"brief": str(args.brief), "pass": not findings, "findings": findings}
    (args.out or args.brief.parent / "ergonomics_check.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(("ERGO PASS " if report["pass"] else "ERGO FAIL ")
          + f"{len(findings)} finding(s)")
    for f in findings:
        print("  -", f)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
