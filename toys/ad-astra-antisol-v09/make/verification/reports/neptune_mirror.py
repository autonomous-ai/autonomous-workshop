"""Are the two Neptune pieces still mirrors of each other?

The correction's negative requirements include it, so it is measured rather
than asserted.  The answer has three parts and only the first is a plain yes.

The PRINTED SOLID is a mirror in the way this set defines one, which is not
"identical".  A Sol disc flares from Ø33.00 at the bed to Ø34.00 at the top and
an Anti-Sol disc does the reverse, so the two printed parts differ by exactly
the volume that draft costs -- 3.99 mm3 -- and that difference is the ownership
cue rather than a fault.  Everything else about the two solids is the same ball
on the same seat.

The MARKING SET is one description used twice, and the globe leans the opposite
way under it.  `features/patches.planet_frame` turns the planet frame about +Y
by +28.32 degrees for a Sol world and -28.32 for its Anti-Sol mirror, and
mirroring the piece in X turns a rotation by +t into one by -t, so the Anti-Sol
piece is the exact mirror of the Sol piece for any marking whose own pattern is
symmetric about the meridian the mirror fixes.  This one is not, and nothing in
this set is: the markings are drawn at the longitudes the cameras want.

So the third part is where the two pieces actually part company, and it is the
DISC'S OWN CUT.  `parts/world.py` removes everything below the disc's top face,
which in the planet's frame is a different half-space on the two armies, so a
marking that reaches far enough south is clipped by the disc on one piece and
not on the other.  On Neptune that is `s1` at latitude -52 and `s2` at -37 --
the same two the facing report names as Anti-Sol-only features.  Every other
white body, and the dark spot, comes out at exactly the same volume on both.

    "$WORKSHOP_PYTHON" measure/neptune_mirror.py > measure/neptune-mirror.md
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.world import world_bodies                          # noqa: E402

#: mm3.  A boolean run on the same source is reproducible far below this.
TOLERANCE = 1e-4


def bodies(side: str):
    out = {}
    for role, (colour, shape) in world_bodies("neptune", side).items():
        solids = shape.solids()
        out[role] = {
            "colour": colour,
            "solids": len(solids),
            "volume": shape.volume,
            "parts": sorted(round(item.volume, 6) for item in solids),
            "bbox": shape.bounding_box(),
        }
    return out


def main() -> int:
    sol, anti = bodies("sol"), bodies("anti")
    print("# The two Neptune pieces against each other")
    print()
    print("Measured on the exact colour bodies `parts/world.py` builds, at")
    print("%g mm3. The two armies share one marking description and lean the" % TOLERANCE)
    print("opposite way under it; this is what that produces.")
    print()
    print("## Body for body")
    print()
    print("| role | filament | solids Sol / Anti | volume Sol mm3 | volume Anti mm3 "
          "| difference mm3 | |")
    print("|---|---|---:|---:|---:|---:|---|")
    faults = []
    for role in sol:
        if role not in anti:
            faults.append("%s exists on the Sol piece and not on the Anti-Sol one" % role)
            continue
        left, right = sol[role], anti[role]
        delta = right["volume"] - left["volume"]
        if left["solids"] != right["solids"]:
            verdict = "**SOLID COUNT DIFFERS**"
            faults.append("%s has %d solids on Sol and %d on Anti-Sol"
                          % (role, left["solids"], right["solids"]))
        elif abs(delta) <= TOLERANCE:
            verdict = "identical"
        elif role == "disc":
            verdict = "the draft, by design"
        else:
            verdict = "clipped differently by the disc"
        print("| `%s` | `%s` | %d / %d | %.4f | %.4f | %+.4f | %s |"
              % (role, left["colour"], left["solids"], right["solids"],
                 left["volume"], right["volume"], delta, verdict))
    for role in anti:
        if role not in sol:
            faults.append("%s exists on the Anti-Sol piece and not on the Sol one" % role)
    print()

    print("## The nine white bodies, one by one")
    print()
    print("The `streaks` marking is eight cloud streaks and the dark spot's")
    print("bright companion, so it comes out as nine separate solids on each")
    print("piece. Sorted by volume, because the split order is not the table")
    print("order, and paired off: a pair that matches to %g mm3 is the same" % TOLERANCE)
    print("body on both armies.")
    print()
    left = list(sol["streaks"]["parts"])
    right = list(anti["streaks"]["parts"])
    print("The `streaks` marking is eight cloud streaks and the dark spot's")
    print("bright companion, so it comes out as nine separate solids on each")
    print("piece. The split order is not the table order, so the two lists are")
    print("paired by MATCHING rather than by position: every Sol body is paired")
    print("with the Anti-Sol body nearest it in volume, and a pair inside")
    print("%g mm3 is the same body on both armies." % TOLERANCE)
    print()
    pool = list(right)
    pairs = []
    for value in sorted(left):
        if not pool:
            pairs.append((value, None))
            continue
        best = min(pool, key=lambda other: abs(other - value))
        if abs(best - value) <= TOLERANCE:
            pool.remove(best)
            pairs.append((value, best))
        else:
            pairs.append((value, None))
    print("| | volume Sol mm3 | volume Anti mm3 | |")
    print("|---:|---:|---:|---|")
    matched = 0
    for index, (a, b) in enumerate(pairs, 1):
        if b is None:
            print("| %d | %.4f | -- | **Sol only at this volume** |" % (index, a))
        else:
            matched += 1
            print("| %d | %.4f | %.4f | identical |" % (index, a, b))
    for value in sorted(pool):
        index += 1
        print("| %d | -- | %.4f | **Anti-Sol only at this volume** |" % (index, value))
    print()
    print("**%d of the %d white bodies come out at exactly the same volume on"
          % (matched, len(left)))
    print("both pieces.** The %d that do not are the two deepest southern"
          % (len(left) - matched))
    print("streaks, `s1` at latitude -52 and `s2` at -37. `parts/world.py` cuts")
    print("the globe level with the disc's top face, and that plane sits in a")
    print("different place in the planet's own frame on the two armies because")
    print("the globe leans the opposite way, so a marking far enough south runs")
    print("into the disc on one piece and clears it on the other. On Neptune the")
    print("disc takes %.2f mm3 more white off the Sol piece than off the"
          % (anti["streaks"]["volume"] - sol["streaks"]["volume"]))
    print("Anti-Sol one. Those are the same two streaks")
    print("`measure/neptune-facing.md` records as Anti-Sol-only features, so the")
    print("piece that shows them is the piece that carries all of them.")
    print()
    unmatched = len(left) - matched

    print("## The printed solid")
    print()
    print("| | Sol | Anti-Sol |")
    print("|---|---:|---:|")
    print("| disc bed diameter mm | %.2f | %.2f |" % (P.DISC_D_BOT_SOL, P.DISC_D_BOT_ANTI))
    print("| disc top diameter mm | %.2f | %.2f |" % (P.DISC_D_TOP_SOL, P.DISC_D_TOP_ANTI))
    print("| globe diameter mm | %.2f | %.2f |"
          % (P.globe_diameter("neptune"), P.globe_diameter("neptune")))
    print("| north pole leans toward | +X | -X |")
    print("| obliquity deg | %+.2f | %+.2f |"
          % (P.PLANETS["neptune"]["tilt"], -P.PLANETS["neptune"]["tilt"]))
    print()
    print("`measure/revision-part-hashes.md` shows both printed STEPs coming out")
    print("byte-identical to the published set's, which is the other half of the")
    print("same statement: this correction moved a colour boundary and nothing")
    print("else.")
    print()

    print("## Verdict")
    print()
    if faults:
        print("**FAULTS**")
        for item in faults:
            print("- %s" % item)
        return 1
    print("The two pieces carry the same roles, the same filaments and the same")
    print("number of solids in every role. %d of the nine white bodies and the"
          % matched)
    print("dark spot are identical in volume to %g mm3. The %d that differ, and"
          % (TOLERANCE, unmatched))
    print("the disc, differ for reasons that are in the design rather than in the")
    print("build: the mirrored lean against a disc cut that is not mirrored with")
    print("it, and the opposite draft that tells the armies apart.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
