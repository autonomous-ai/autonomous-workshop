"""Re-Pin (g0002) — the brief §8 64-pair test, run on the built solids.

The brief makes GP1's physical 64/64 a hard gate.  No printer ran in this build,
so this script runs the *same* 64 (pin, slider) pairs against the *same*
geometry the printer would get — `build_gp1_plug()`, `build_gp1_shell()`,
`build_pin()`, `build_slug()` — as exact B-rep booleans, and reports the angle
at which each pair stops.  It is a geometric proof, not a physical one: it
cannot see warp, elephant's foot, layer adhesion or friction, and it does not
retire the print.  What it does retire is "the mechanism is unconfirmed by
anything": every pair either rides to the wall or does not, measured.

Two sections:

  §8  the 64 pairs on the GP1 test cell (one chamber, one 36° notch/channel)
      pass = matched pairs free through 90°, mismatched pairs riding at 34°
      and dead at 38° — which is the brief's own ±2° repeatability window.

  §1  the ordinal table on the *full* five-chamber lock: the plug stops at S of
      the lowest-index wrong chamber, and the chambers after it have zero
      effect on the angle.

Run:  $BOB_CAD_PY measure/check_ladder.py [--pairs N] [--json]
Exit 0 = every case landed where the brief says it must.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[2] / "skills" / "cad" / "scripts"))

import repin_lib as lib
from build123d import Box, Pos, Rot

# A B-rep intersection of two parts that only touch is exactly zero volume, so
# the tolerance only has to swallow numeric noise from the chorded sectors.
TOL = 0.05          # mm³
WINDOW = 2.0        # the brief's ±2° repeatability window
GP1_S = lib.GP1_STOP


def vol(shape) -> float:
    solids = shape.solids() if shape is not None else []
    return float(sum(s.volume for s in solids))


def overlap(a, b) -> float:
    """Exact intersection volume.  Unlike the gate's helper this one does not
    swallow boolean failures — a failed boolean must not read as 'clear'."""
    ba, bb = a.bounding_box(), b.bounding_box()
    if (ba.min.X > bb.max.X or ba.max.X < bb.min.X
            or ba.min.Y > bb.max.Y or ba.max.Y < bb.min.Y
            or ba.min.Z > bb.max.Z or ba.max.Z < bb.min.Z):
        return 0.0
    return vol(a & b)


# ---------------------------------------------------------------------------
# the drop: where a pin and a driver actually come to rest, measured
# ---------------------------------------------------------------------------
def pin_bottom(setting: int) -> float:
    """The pin rests on the key lifter for `setting`."""
    return lib.LIFTER_TOP_Y[setting - 1]


def nose_rest(rung: int, setting: int) -> float:
    """Driver nose height: on the pin top, or on the notch floor if the pin has
    fallen further than the notch is deep.  Both supports are verified below by
    dropping the driver 0.3 mm and requiring it to foul."""
    on_pin = lib.R_SHEAR + lib.LADDER_STEP * (rung - setting)
    return max(on_pin, lib.NOTCH_FLOOR_R)


def cell(rung: int, setting: int, theta: float, zc: float = lib.GP1_ZC):
    """(rotating group, static group) for one chamber at plug angle `theta`.

    The pin lives in the plug bore and turns with it; the driver is held by the
    shell chimney and does not."""
    turn = Rot(0, 0, theta)
    pin = (Pos(0, 0, zc) * Rot(-90, 0, 0) * Pos(0, 0, pin_bottom(setting))
           * lib.build_pin(rung))
    slug = (Pos(0, 0, zc) * Rot(-90, 0, 0) * Pos(0, 0, nose_rest(rung, setting))
            * lib.build_slug())
    return turn * pin, slug


# ---------------------------------------------------------------------------
# §8 — the 64 pairs on the GP1 cell
# ---------------------------------------------------------------------------
def run_pairs(limit: int | None = None) -> tuple[list[dict], list[str]]:
    plug0 = lib.build_gp1_plug()
    shell = lib.build_gp1_shell()
    rows, fails = [], []

    pairs = list(itertools.product(range(1, lib.RUNGS + 1), repeat=2))
    if limit:
        pairs = pairs[:limit]

    for rung, setting in pairs:
        matched = rung == setting
        pin0, slug = cell(rung, setting, 0.0)

        # 1. the driver is really resting on something: clear where it sits,
        #    fouled 0.3 mm lower.  This is the gravity feed, checked.
        seated = overlap(slug, plug0) + overlap(slug, pin0)
        low = Pos(0, -0.3, 0) * slug
        supported = overlap(low, plug0) + overlap(low, pin0)

        # 2. where does it stop?  Clear just inside the wall, dead just outside.
        angles = {}
        for theta in (GP1_S - WINDOW, GP1_S + WINDOW, lib.OPEN_ANGLE):
            pin, _ = cell(rung, setting, theta)
            plug = Rot(0, 0, theta) * plug0
            angles[theta] = round(
                overlap(plug, slug) + overlap(pin, shell)
                + overlap(pin, slug) + overlap(plug, shell), 4)

        want_blocked = not matched
        ok_seat = seated <= TOL and supported > TOL
        ok_ride = angles[GP1_S - WINDOW] <= TOL
        ok_wall = (angles[GP1_S + WINDOW] > TOL) == want_blocked
        ok_open = (angles[lib.OPEN_ANGLE] > TOL) == want_blocked

        row = dict(rung=rung, setting=setting, error_rungs=rung - setting,
                   matched=matched, noseMm=round(nose_rest(rung, setting), 3),
                   pinTopMm=round(pin_bottom(setting) + lib.PIN_HEIGHTS[rung - 1], 3),
                   seatedMm3=round(seated, 4), supportMm3=round(supported, 4),
                   atMinusMm3=angles[GP1_S - WINDOW],
                   atPlusMm3=angles[GP1_S + WINDOW],
                   atOpenMm3=angles[lib.OPEN_ANGLE],
                   verdict="free" if not want_blocked else "stops",
                   ok=bool(ok_seat and ok_ride and ok_wall and ok_open))
        rows.append(row)
        if not row["ok"]:
            fails.append(
                f"pin r{rung} / slider {setting}: seat={ok_seat} ride={ok_ride} "
                f"wall={ok_wall} open={ok_open} {row}")
        print(f"  r{rung} s{setting} {'=' if matched else ' '} "
              f"nose {row['noseMm']:6.2f}  {GP1_S - WINDOW:.0f}°"
              f" {row['atMinusMm3']:9.3f}  {GP1_S + WINDOW:.0f}°"
              f" {row['atPlusMm3']:9.3f}  90° {row['atOpenMm3']:9.3f}"
              f"   {'ok' if row['ok'] else 'FAIL'}", flush=True)
    return rows, fails


# ---------------------------------------------------------------------------
# §1 — the ordinal table on the full lock
# ---------------------------------------------------------------------------
# (settings, expected first wrong chamber index or None) — the last three share
# a first mistake and differ downstream, which is the "zero effect" claim.
ORDINAL = [
    ((8, 1, 2, 3, 4), 0),
    ((1, 8, 2, 3, 4), 1),
    ((1, 2, 8, 3, 4), 2),
    ((1, 2, 3, 8, 4), 3),
    ((1, 2, 3, 4, 8), 4),
    ((1, 2, 3, 4, 5), None),
    ((1, 5, 3, 4, 5), 1),      # same first mistake as the next two ...
    ((1, 5, 8, 8, 8), 1),      # ... every later chamber wrong ...
    ((1, 5, 3, 4, 5), 1),      # ... and right again: the angle must not move
]
LOADED = (1, 2, 3, 4, 5)       # the pins in the lock for the ordinal runs


def run_ordinal() -> tuple[list[dict], list[str]]:
    plug0 = lib.build_plug()
    shell = lib.build_shell()
    rows, fails = [], []

    for settings, first_wrong in ORDINAL:
        expect = lib.OPEN_ANGLE if first_wrong is None else lib.STOPS[first_wrong]
        drivers, pins0 = [], []
        for i, (r, s) in enumerate(zip(LOADED, settings)):
            pin, slug = cell(r, s, 0.0, zc=lib.CHAMBER_X[i])
            pins0.append((r, s, i))
            drivers.append(slug)

        angles = {}
        for theta in (expect - WINDOW, expect + WINDOW):
            plug = Rot(0, 0, theta) * plug0
            total = overlap(plug, shell)
            for r, s, i in pins0:
                pin, _ = cell(r, s, theta, zc=lib.CHAMBER_X[i])
                total += overlap(pin, shell)
                for slug in drivers:
                    total += overlap(pin, slug)
            for slug in drivers:
                total += overlap(plug, slug)
            angles[theta] = round(total, 4)

        open_case = first_wrong is None
        ok = (angles[expect - WINDOW] <= TOL
              and (angles[expect + WINDOW] > TOL) != open_case)
        rows.append(dict(settings=list(settings), firstWrong=first_wrong,
                         expectDeg=expect,
                         beforeMm3=angles[expect - WINDOW],
                         afterMm3=angles[expect + WINDOW], ok=bool(ok)))
        if not ok:
            fails.append(f"settings {settings}: expected a stop at {expect}°, "
                         f"got {angles}")
        print(f"  settings {settings}  first wrong "
              f"{'-' if open_case else first_wrong + 1}  expect {expect:5.1f}°"
              f"   {expect - WINDOW:5.1f}° {angles[expect - WINDOW]:9.3f}"
              f"   {expect + WINDOW:5.1f}° {angles[expect + WINDOW]:9.3f}"
              f"   {'ok' if ok else 'FAIL'}", flush=True)
    return rows, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=None,
                    help="only the first N of the 64 pairs (timing runs)")
    ap.add_argument("--skip-ordinal", action="store_true")
    ap.add_argument("--json", default=None, help="write the full table here")
    args = ap.parse_args()

    t0 = time.time()
    print(f"§8  GP1 cell — 64 (pin, slider) pairs, stop wall at {GP1_S}°, "
          f"window ±{WINDOW}°")
    rows, fails = run_pairs(args.pairs)
    n_ok = sum(1 for r in rows if r["ok"])
    print(f"  {n_ok}/{len(rows)} pairs land where the brief says "
          f"({time.time() - t0:.0f}s)")

    ord_rows: list[dict] = []
    if not args.skip_ordinal:
        print(f"\n§1  ordinal table — the full five-chamber lock")
        ord_rows, ord_fails = run_ordinal()
        fails += ord_fails
        print(f"  {sum(1 for r in ord_rows if r['ok'])}/{len(ord_rows)} "
              f"configurations stop at the briefed angle")

    if args.json:
        Path(args.json).write_text(json.dumps(
            dict(pairs=rows, ordinal=ord_rows, tolMm3=TOL, windowDeg=WINDOW,
                 pairsOk=n_ok, pairsTotal=len(rows)), indent=2))

    print(f"\ntotal {time.time() - t0:.0f}s")
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print(" ", f)
        return 1
    print("ok — every case landed where the brief says it must "
          "(geometry only; the print is still owed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
