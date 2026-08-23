"""Per-project fit audit for CLEARANCE (g0003).

The generic gates own the geometry claims — `check_layout` owns the file split,
`check_fit` owns bed datum / footprint / body count, `check_mesh` owns watertight
and winding, `inspect interfere` owns overlap. None of them can check the things
that make THIS box a game, so those live here and are algebraic:

  1. every brief §3 coupled pair (delegated to clearance_lib._check_params)
  2. the §3.3 margin guarantee on this copy's block ladder
  3. bill <-> parts: one part_<part_id>.step.py per printed part_id, exactly
  4. print envelope per part, including the 45 deg yaw a 220 bed needs for the
     yoke — the one part that does not fit a 220 bed axis-aligned

    $BOB_CAD_PY measure/check_fit.py        # non-zero exit on any failure
"""

from __future__ import annotations

import math
import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # parts/
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.normpath(
    os.path.join(_HERE, "..", "..", "..", "skills", "cad", "scripts")))

import clearance_lib as lib   # noqa: E402 — import runs _check_params + _check_ladder

BRIEF_BED = 251.0     # brief §2: bed 256, every part fits 251 x 251 x 251 flat
SHOP_BED = 220.0      # the smaller machine the generic gate assumes

# brief §2 envelope column, x-by-y-by-z, as written
BRIEF_ENVELOPE = {
    "gantry_base": (220.0, 78.0, 10.0),
    "column_screw": (44.0, 44.0, 104.0),
    "detent_leaf": (34.0, 12.0, 4.0),
    "post_guide": (12.0, 12.0, 82.0),
    "yoke": (224.0, 34.0, 62.0),
    "stop_ring": (36.0, 36.0, 2.75),
    "knob_hood": (82.0, 82.0, 84.0),
    "rail_01": (178.0, 32.0, 8.0),
}

fails: list[str] = []
notes: list[str] = []


def check(cond: bool, msg: str) -> None:
    (notes if cond else fails).append(("PASS  " if cond else "FAIL  ") + msg)


# -- 1. coupled pairs ------------------------------------------------------
lib._check_params()
check(True, "brief §3 coupled pairs: clearance_lib._check_params() all assertions hold")

# -- 2. the margin guarantee ----------------------------------------------
# §3.3 says H_top cancels out. Prove it: re-run the ladder check at three
# different measured H_top values, which is the whole claim.
for h_top in (32.50, 33.00, 33.50):
    lib._check_ladder(h_top)
bars = [lib.H_TOP_NOM - 0.5 * k for k in range(32)]
worst = min(abs(h - b) for h in lib.PIECE_LADDER.values() for b in bars)
check(worst >= 0.2499,
      f"§3.3 margin guarantee: worst block-vs-bar margin {worst:.4f} mm >= 0.25, "
      f"and it holds at H_top = 32.50 / 33.00 / 33.50")

# -- 3. bill <-> parts -----------------------------------------------------
present = {f[len("part_"):-len(".step.py")]
           for f in os.listdir(_HERE)
           if f.startswith("part_") and f.endswith(".step.py")}
expected = set(lib.PART_IDS)
missing = sorted(expected - present)
check(not missing, f"every printed part_id has a part_<id>.step.py ({len(expected)} ids)"
      + (f" — MISSING {missing}" if missing else ""))
extra = sorted(present - expected - {"golden_stub"})
check(not extra, "no part entry outside the bill" + (f" — EXTRA {extra}" if extra else ""))
check("golden_stub" in present,
      "golden_stub present — brief 'the wound comes first': column_screw + "
      "detent_leaf + a 60x60 stub with a dial-indicator post")

# -- 3b. §4.1 hidden state: the knob is not visible from above -------------
# Not an algebraic claim — a real solid test. Sweep the knob's whole D44.40 seat
# circle up through the roof and assert the hood fills EVERY cubic millimetre of
# it. If any part of that column is void, a seat looking down the screw axis
# reads the knob's rotation, which is the game's only secret.
from build123d import Cylinder, Pos, Align   # noqa: E402

_hood = lib.build_knob_hood()
_sight = Pos(lib.SCREW_X, 0, lib.HOOD_SEAT_Z) * Cylinder(
    lib.HOOD_LEDGE_D / 2, lib.HOOD_CAP_T,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
_want = _sight.volume
_got = (_hood & _sight).volume
check(abs(_got - _want) / _want < 1e-4,
      f"§4.1 no sightline to the knob: the D{lib.HOOD_LEDGE_D:.2f} column from the "
      f"knob top face (Z {lib.HOOD_SEAT_Z:.0f}) to the roof (Z {lib.HOOD_TOP_Z:.1f}) is "
      f"{100 * _got / _want:.2f}% solid hood, want 100.00%")

# and the same column must be void just BELOW the seat, or the hood cannot drop
# onto the knob at all
_pocket = Pos(lib.SCREW_X, 0, lib.HOOD_SEAT_Z - 10.0) * Cylinder(
    lib.KNOB_D / 2, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN),
)
_blocked = (_hood & _pocket).volume
check(_blocked / _pocket.volume < 1e-4,
      f"the hood still drops over the D{lib.KNOB_D:.0f} knob: "
      f"{100 * _blocked / _pocket.volume:.2f}% obstructed, want 0.00%")

# -- 4. print envelope -----------------------------------------------------
rows = []
for pid, (bx, by, bz) in BRIEF_ENVELOPE.items():
    fn = getattr(lib, "print_" + pid.rstrip("_01234"), None) or getattr(
        lib, "print_" + pid.rsplit("_", 1)[0], None)
    bb = fn().bounding_box()
    x, y, z = bb.size.X, bb.size.Y, bb.size.Z
    flat = max(x, y) <= BRIEF_BED and z <= BRIEF_BED
    yaw = (x + y) / math.sqrt(2.0)
    rows.append((pid, x, y, z, bx, by, bz, flat, yaw))
    check(flat, f"{pid}: {x:.1f} x {y:.1f} x {z:.1f} fits the brief's {BRIEF_BED:.0f} bed flat")
    if max(x, y) > SHOP_BED:
        check(yaw <= SHOP_BED and z <= 250.0,
              f"{pid}: exceeds a {SHOP_BED:.0f} bed axis-aligned, needs 45 deg yaw "
              f"-> {yaw:.1f} mm square footprint")

print("part            built x    y     z   | brief x    y     z   | 220-bed")
for pid, x, y, z, bx, by, bz, flat, yaw in rows:
    tag = "flat" if max(x, y) <= SHOP_BED else f"yaw 45 -> {yaw:.0f}"
    print(f"{pid:14s} {x:7.1f}{y:6.1f}{z:6.1f} | {bx:7.1f}{by:6.1f}{bz:6.1f} | {tag}")
print()
for line in notes:
    print(line)
for line in fails:
    print(line)
print()
print(f"check_fit.py: {len(notes)} pass, {len(fails)} fail")
sys.exit(1 if fails else 0)
