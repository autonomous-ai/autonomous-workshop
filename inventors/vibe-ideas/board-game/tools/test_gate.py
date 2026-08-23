#!/usr/bin/env python3
"""test_gate.py — regression fixtures for the acceptance gate.

    .venv/bin/python board-game/tools/test_gate.py

Every case here exists because the gate got it wrong once. Prints ALL PASS or
the failing cases; exit 0/1. improve.py must see ALL PASS before any change to
gate.py is kept.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
GATE = HERE / "gate.py"
PY = REPO_ROOT / ".venv" / "bin" / "python"

# (name, source, bill, expect_pass, substrings that must appear in fails,
#  [motions], [brief], [substrings in `unmeasured` — prefix "!" for must NOT])
#
# The last field is about the other half of a verdict. `unmeasured` is what a
# check could not reach a conclusion on, and it never fails the gate, so it has
# exactly the shape of a thing that rots unnoticed: both a check that stopped
# firing and a check that fires on everything look like a pass from here.
CASES = [
    (
        "separate_pieces",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    for i in range(4):
        asm.add(cq.Workplane("XY").box(40, 40, 4), name=f"tile_{i+1:02d}",
                loc=cq.Location(cq.Vector(i * 45, 0, 0)))
    return asm
""",
        [{"name": "tile", "qty": 4}],
        True, [],
        None, None,
        # Pieces with air between them are fully measurable, so a clean build
        # must report nothing unmeasured about interference. Without this, a
        # check that quietly went inconclusive on every project would still
        # look exactly like this suite passing.
        ["!interference"],
    ),
    (
        # The failure that destroyed turns 11-15: pieces the rules need loose
        # arriving welded into one body.
        "fused_mat",
        """import cadquery as cq
def gen_step():
    mat = cq.Workplane("XY").box(40, 40, 4)
    for i in range(1, 4):
        mat = mat.union(cq.Workplane("XY").box(40, 40, 4).translate((i * 40, 0, 0)))
    return mat
""",
        [{"name": "tile", "qty": 4}],
        False, ["unioned together"],
    ),
    (
        # A single-piece game is legitimate, and cadcode collapses a one-child
        # assembly to an unnamed model — that must not read as fusion.
        "single_piece_is_fine",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(120, 120, 8), name="board")
    return asm
""",
        [{"name": "board", "qty": 1}],
        True, [],
    ),
    (
        "over_bed",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(300, 300, 10), name="board")
    return asm
""",
        [{"name": "board", "qty": 1}],
        False, ["envelope", "does not fit"],
    ),
    (
        "part_in_two_lumps",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    two = cq.Workplane("XY").box(20, 20, 4).union(
        cq.Workplane("XY").box(20, 20, 4).translate((100, 0, 0)))
    asm.add(two, name="token_01")
    return asm
""",
        [{"name": "token", "qty": 1}],
        False, ["disconnected bodies"],
    ),
    (
        # A lid modelled resting on its box has its whole underside facing
        # down; measuring as-modelled would fail a part that prints fine
        # flipped over.
        "orientation_is_chosen_not_assumed",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    lid = cq.Workplane("XY").box(80, 60, 3).faces("<Z").workplane().rect(
        74, 54).extrude(6)
    asm.add(lid, name="lid")
    return asm
""",
        [{"name": "lid", "qty": 1}],
        True, [],
    ),
    (
        # Two parts that were never booleaned together, simply drawn through
        # each other: a peg driven through a solid plate. Every per-part check
        # passes — both are one closed printable body — so nothing but the
        # interference step can see it. This is the Armillary defect's shape.
        "peg_driven_through_plate",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(60, 60, 6), name="plate")
    asm.add(cq.Workplane("XY").circle(5).extrude(30), name="peg",
            loc=cq.Location(cq.Vector(0, 0, -15)))
    return asm
""",
        [{"name": "plate", "qty": 1}, {"name": "peg", "qty": 1}],
        False, ["interference", "shared volume"],
    ),
    (
        # The same peg through a hole sized for it. A clearance fit must not
        # read as interference, or every socket in every game fails the gate.
        "peg_in_clearance_hole_is_fine",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(60, 60, 6).faces(">Z").workplane().hole(12),
            name="plate")
    asm.add(cq.Workplane("XY").circle(5).extrude(30), name="peg",
            loc=cq.Location(cq.Vector(0, 0, -15)))
    return asm
""",
        [{"name": "plate", "qty": 1}, {"name": "peg", "qty": 1}],
        True, [],
    ),
    (
        # A windowed disc turning over standing pegs. In the pose it is exported
        # in, every peg sits centred in a window and the assembly is spotless —
        # so no single-pose check can fault it. Turn the disc half an index step
        # and every peg is buried. This is Armillary's defect in miniature, and
        # it is the case that proves the gate looks at more than one pose.
        "windowed_disc_jams_when_turned",
        """import cadquery as cq
import math
RING_R, HOLES = 30.0, 6
def gen_step():
    asm = cq.Assembly()
    mask = cq.Workplane("XY").circle(45).extrude(8)
    for k in range(HOLES):
        a = math.radians(k * 360.0 / HOLES)
        mask = mask.cut(cq.Workplane("XY").circle(6).extrude(8).translate(
            (RING_R * math.cos(a), RING_R * math.sin(a), 0)))
    asm.add(mask, name="mask")
    for k in range(HOLES):
        a = math.radians(k * 360.0 / HOLES)
        asm.add(cq.Workplane("XY").circle(4).extrude(17), name=f"peg_{k+1:02d}",
                loc=cq.Location(cq.Vector(
                    RING_R * math.cos(a), RING_R * math.sin(a), -5)))
    return asm
""",
        [{"name": "mask", "qty": 1}, {"name": "peg", "qty": 6}],
        False, ["motion", "clear at rest"],
        [{"part": "mask", "kind": "rotation",
          "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
          "range_deg": [0, 60], "steps": 6}],
    ),
    (
        # A disc free-spinning on its post: clean at rest and clean at every
        # angle, so the geometry is not the point. The brief says it TURNS and
        # the project never declared the turn, which means the sweep ran over
        # nothing and the gate's pass would be about a motion it never looked
        # at. Forgetting the declaration has to cost as much as failing it, or
        # the cheapest way past the check is to say nothing.
        "brief_declares_a_turn_that_is_never_swept",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").circle(40).extrude(6).faces(">Z").workplane().hole(12),
            name="mask")
    asm.add(cq.Workplane("XY").circle(5).extrude(20), name="post",
            loc=cq.Location(cq.Vector(0, 0, -7)))
    return asm
""",
        [{"name": "mask", "qty": 1}, {"name": "post", "qty": 1}],
        False, ["mask", "motion.json"],
        None,
        {"interfaces": [{"kind": "turns", "piece": "mask", "about": "post",
                         "range_deg": [0, 360],
                         "notes": "the mask spins freely on the post"}]},
    ),
    (
        # The same geometry with the turn actually declared. The sweep runs,
        # finds nothing, and the pass now means something.
        "declared_turn_that_never_collides_passes",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").circle(40).extrude(6).faces(">Z").workplane().hole(12),
            name="mask")
    asm.add(cq.Workplane("XY").circle(5).extrude(20), name="post",
            loc=cq.Location(cq.Vector(0, 0, -7)))
    return asm
""",
        [{"name": "mask", "qty": 1}, {"name": "post", "qty": 1}],
        True, [],
        [{"part": "mask", "kind": "rotation",
          "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
          "range_deg": [0, 360], "steps": 8}],
        {"interfaces": [{"kind": "turns", "piece": "mask", "about": "post",
                         "range_deg": [0, 360]}]},
    ),
    (
        # Graduated lesson: a blanket fillet over every edge direction makes
        # OCCT build spherical vertex blends that tessellate into phantom
        # slivers. It must fail on the source, not wait for the mesh.
        "blanket_fillet_lint",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(40, 40, 20).edges().fillet(2), name="block")
    return asm
""",
        [{"name": "block", "qty": 1}],
        False, ["lint", "blanket"],
    ),
    (
        # Two pieces placed touching. Each part is one closed body, the bill
        # matches, nothing overlaps — and the interference check still cannot
        # say so, because a shared face welds the assembled mesh and the pairs
        # it would have compared stop existing.
        #
        # The verdict is PASS and that is correct; failing here would fail
        # every design whose pieces rest against each other, which is how a
        # gate gets routed around. What must not happen is the pass being
        # indistinguishable from one where the check ran. `unmeasured` is that
        # difference, and it is what pipeline_queue.py refuses to ship on
        # without a human's stated acceptance.
        "touching_pieces_leave_interference_unmeasured",
        """import cadquery as cq
def gen_step():
    asm = cq.Assembly()
    asm.add(cq.Workplane("XY").box(40, 40, 4), name="tile_01")
    asm.add(cq.Workplane("XY").box(40, 40, 4), name="tile_02",
            loc=cq.Location(cq.Vector(40, 0, 0)))
    return asm
""",
        [{"name": "tile", "qty": 2}],
        True, [],
        None, None,
        ["interference", "pairs among any welded or fused pieces"],
    ),
]


def run_case(tmp: Path, name: str, source: str, bill: list,
             motions: list | None = None,
             brief: dict | None = None) -> tuple[bool, list, list]:
    home = tmp / name
    home.mkdir(parents=True)
    (home / "main.py").write_text(source, encoding="utf-8")
    (home / "bill.json").write_text(json.dumps({"components": bill}), encoding="utf-8")
    if motions:
        (home / "motion.json").write_text(json.dumps({"motions": motions}),
                                          encoding="utf-8")
    if brief:
        (home / "brief.json").write_text(json.dumps(brief), encoding="utf-8")
    python = str(PY) if PY.is_file() else sys.executable
    subprocess.run([python, str(GATE), str(home / "main.py"),
                    "--bill", str(home / "bill.json"), "--no-slice"],
                   capture_output=True, text=True, timeout=600)
    report = json.loads((home / "gate.json").read_text(encoding="utf-8"))
    return (bool(report.get("pass")), report.get("fails") or [],
            report.get("unmeasured") or [])


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for case in CASES:
            name, source, bill, expect_pass, needles = case[:5]
            motions = case[5] if len(case) > 5 else None
            brief = case[6] if len(case) > 6 else None
            un_needles = case[7] if len(case) > 7 else []
            passed, fails, unmeasured = run_case(tmp, name, source, bill,
                                                 motions, brief)
            blob = " ".join(fails).lower()
            missing = [n for n in needles if n.lower() not in blob]
            un_blob = " ".join(unmeasured).lower()
            un_wrong = [f"unexpected {n[1:]}" for n in un_needles
                        if n.startswith("!") and n[1:].lower() in un_blob]
            un_wrong += [f"missing {n}" for n in un_needles
                         if not n.startswith("!") and n.lower() not in un_blob]
            if passed != expect_pass:
                failures.append(f"{name}: expected {'PASS' if expect_pass else 'FAIL'}, "
                                f"got {'PASS' if passed else 'FAIL'} ({fails})")
            elif missing:
                failures.append(f"{name}: verdict right but reason missing {missing} "
                                f"in {fails}")
            elif un_wrong:
                failures.append(f"{name}: verdict right but `unmeasured` wrong "
                                f"({un_wrong}) in {unmeasured}")
            else:
                print(f"  ok  {name}")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nALL PASS ({len(CASES)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
