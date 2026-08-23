#!/usr/bin/env python3
"""testbench.py — every golden block, built for real and put through gate.py.

    .venv/bin/python board-game/blocks/testbench.py

A block is only golden if the gate that judges products also passes it. So
this does not assert on the library's internals; it writes a real project per
block, builds it through cadcode, and requires GATE PASS. If a threshold in
gate.py tightens, the blocks have to earn their place again — which is the
point.

improve.py must see ALL PASS here before any change is kept.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
GATE = REPO_ROOT / "board-game" / "tools" / "gate.py"
ERGO = REPO_ROOT / "board-game" / "tools" / "ergonomics_check.py"
PY = REPO_ROOT / ".venv" / "bin" / "python"

sys.path.insert(0, str(REPO_ROOT / "cadcode"))
sys.path.insert(0, str(HERE))

from blocks import seated_pair  # noqa: E402

# The fixtures are source text copied into a throwaway project, so each makes
# its own seated_pair call. These are for the BRIEFS below, which used to state
# the same dimensions by hand and could therefore drift away from the geometry
# they judge — the exact drift seated_pair exists to stop.
PIECE_D, SEAT_D = seated_pair(20.0)

# --- one fixture per block, then one for the blocks together ----------------

FAMILY = """import cadquery as cq
from blocks import shared_positions, add_piece_family

def gen_step():
    asm = cq.Assembly()
    token = cq.Workplane("XY").cylinder(6, 10)
    add_piece_family(asm, token, shared_positions(4, 3, 30), "token")
    return asm
"""

WELLS = """import cadquery as cq
from blocks import shared_positions, add_piece_family, cut_wells, seated_pair

BOARD_T = 8.0
# The seat is DERIVED from the piece, not chosen beside it. This fixture used
# to state diameter=26 for a 20mm token — 3.0mm per side, against the 0.40mm
# seated_pair hands out — so the golden fixture demonstrated a clearance the
# golden library would never produce.
PIECE_D, SEAT_D = seated_pair(20.0)

def gen_step():
    # ONE position list feeds both the wells and the pieces that sit in them.
    seats = shared_positions(4, 3, 40)
    board = cq.Workplane("XY").box(200, 150, BOARD_T).translate((0, 0, BOARD_T / 2))
    board = cut_wells(board, seats, diameter=SEAT_D, depth=5, top_z=BOARD_T)
    asm = cq.Assembly()
    asm.add(board, name="board")
    token = cq.Workplane("XY").cylinder(10, PIECE_D / 2)
    add_piece_family(asm, token, seats, "token", lift=BOARD_T)
    return asm
"""

TILED_WELLS = """import cadquery as cq
from blocks import (add_piece_family, cut_wells, seated_pair, shared_positions,
                    tiled_board)

BOARD_W, BOARD_D, BOARD_T = 500.0, 300.0, 8.0
PIECE_D, SEAT_D = seated_pair(20.0)

def gen_step():
    # Three blocks at once: a board too big for the bed, seats in it, and the
    # pieces those seats hold. The seat grid is chosen to clear every tile seam
    # — see test_checks.compose_tiled_wells for why nothing else would notice
    # if it did not.
    asm = cq.Assembly()
    seats = shared_positions(4, 2, 100.0)
    for tile in tiled_board(BOARD_W, BOARD_D, BOARD_T):
        slab = (cq.Workplane("XY")
                .box(tile["w"] - 0.4, tile["d"] - 0.4, tile["t"])
                .translate((tile["x"], tile["y"], tile["t"] / 2)))
        mine = [(x, y, 0.0) for x, y, _ in seats
                if abs(x - tile["x"]) < tile["w"] / 2
                and abs(y - tile["y"]) < tile["d"] / 2]
        slab = cut_wells(slab, mine, diameter=SEAT_D, depth=5.0, top_z=tile["t"])
        asm.add(slab, name=tile["name"])
    token = cq.Workplane("XY").cylinder(10, PIECE_D / 2)
    add_piece_family(asm, token, seats, "token", lift=BOARD_T)
    return asm
"""

SEATED = """import cadquery as cq
from blocks import seated_pair

PEG_D, HOLE_D = seated_pair(10.0)
assert HOLE_D > PEG_D, "the seat must be larger than the piece"
assert HOLE_D - PEG_D < 1.0, "a 4x-clearance seat means both halves drifted"

def gen_step():
    asm = cq.Assembly()
    plate = cq.Workplane("XY").box(80, 80, 10).translate((0, 0, 5))
    plate = plate.cut(cq.Workplane("XY").cylinder(10, HOLE_D / 2).translate((0, 0, 5)))
    asm.add(plate, name="plate")
    asm.add(cq.Workplane("XY").cylinder(20, PEG_D / 2), name="peg_01",
            loc=cq.Location(cq.Vector(0, 0, 10)))
    return asm
"""

TILED = """import cadquery as cq
from blocks import tiled_board

def gen_step():
    asm = cq.Assembly()
    for tile in tiled_board(500, 300, 8):
        asm.add(cq.Workplane("XY").box(tile["w"] - 0.4, tile["d"] - 0.4, tile["t"]),
                name=tile["name"],
                loc=cq.Location(cq.Vector(tile["x"], tile["y"], 0)))
    return asm
"""

CASES = [
    ("add_piece_family", FAMILY, [{"name": "token", "qty": 12}]),
    ("cut_wells", WELLS, [{"name": "board", "qty": 1}, {"name": "token", "qty": 12}]),
    ("seated_pair", SEATED, [{"name": "plate", "qty": 1}, {"name": "peg", "qty": 1}]),
    ("tiled_board", TILED, [{"name": "board_tile", "qty": 6}]),
    # Not a block, a composition: the only fixture where three of them meet.
    # test_checks.COMPOSITIONS names it, and fails if it stops existing.
    ("tiled_wells", TILED_WELLS,
     [{"name": "board_tile", "qty": 6}, {"name": "token", "qty": 8}]),
]

# The wells block exists to satisfy R2, so it is held to R2 as well as to the
# gate: a seat a hand cannot reach into is not a golden block. The numbers come
# from the same seated_pair call the fixture builds from, so the brief cannot
# drift away from the geometry it is judging.
WELLS_BRIEF = {"parts": [
    {"name": "token", "kind": "loose_piece", "bbox_mm": [PIECE_D, PIECE_D, 10]},
    {"name": "board", "kind": "board", "bbox_mm": [200, 150, 8],
     "recesses": [{"holds": "token", "width_mm": SEAT_D, "depth_mm": 5,
                   "count": 12}]},
]}


def python() -> str:
    return str(PY) if PY.is_file() else sys.executable


def run_case(tmp: Path, name: str, source: str, bill: list) -> tuple[bool, list]:
    home = tmp / name
    home.mkdir(parents=True)
    (home / "main.py").write_text(source, encoding="utf-8")
    # Blocks are copied INTO the project, never imported across the repo: a
    # shipped project has to stay reproducible after the library moves on.
    shutil.copy2(HERE / "blocks.py", home / "blocks.py")
    (home / "bill.json").write_text(json.dumps({"components": bill}), encoding="utf-8")
    subprocess.run([python(), str(GATE), str(home), "--bill", str(home / "bill.json"),
                    "--no-slice"], capture_output=True, text=True, timeout=900)
    report = json.loads((home / "gate.json").read_text(encoding="utf-8"))
    return bool(report.get("pass")), report.get("fails") or []


def main() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name, source, bill in CASES:
            passed, fails = run_case(tmp, name, source, bill)
            if passed:
                print(f"  ok  {name}")
            else:
                failures.append(f"{name}: GATE FAIL {fails}")

        brief = tmp / "wells_brief.json"
        brief.write_text(json.dumps(WELLS_BRIEF), encoding="utf-8")
        r = subprocess.run([python(), str(ERGO), str(brief)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print("  ok  cut_wells/ergonomics")
        else:
            failures.append(f"cut_wells/ergonomics: {r.stdout.strip()}")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nALL PASS ({len(CASES) + 1} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
