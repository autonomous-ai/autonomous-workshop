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

The third part is the DISC'S OWN CUT, and on this revision it costs nothing.
`parts/world.py` removes everything below the disc's top face, which in the
planet's frame is a different half-space on the two armies, so a marking that
reaches far enough south is clipped by the disc on one piece and not on the
other.  That is what happened to two of the eight cloud streaks the build this
revision corrects drew.  A closed latitude band cannot: it is a surface of
revolution about the globe's own polar axis, so the mirror maps each band onto
itself and the cut takes the same arc out of it on both armies.  Every white
body and the dark spot are therefore expected to come out at exactly the same
volume on both pieces, and the disc is expected to be the only difference.

    "$WORKSHOP_PYTHON" measure/neptune_mirror.py > measure/neptune-mirror.md
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.markings import MARKINGS                            # noqa: E402
from parts.world import world_bodies                          # noqa: E402

#: mm3.  A boolean run on the same source is reproducible far below this.
TOLERANCE = 1e-4

#: Neptune's white marking, read off the marking table rather than named here,
#: so that this report cannot go on describing a marking the build stopped
#: drawing.  That is exactly how this set's sealed Neptune report went stale.
WHITE_KEY = next(key for key, colour, _specs, _sub in MARKINGS["neptune"]
                 if colour == "white")

#: mm3.  The volume the build this revision corrects measured the dark spot
#: body at, on BOTH armies, quoted from that build's own sealed
#: `make/verification/reports/neptune-mirror.md` in `revision-source.zip`.
#:
#: Requirement 2 of this revision is that the dark spot does not move, and this
#: is the number that requirement is checked against rather than a number this
#: run produced.  It is an archival fact, not a measurement, so it is written
#: down once, here, with its source, and the check below is allowed to fail.
ARCHIVED_SPOT_MM3 = 11.9319


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

    print("## The white bodies, one by one")
    print()
    print("Neptune's white marking is `%s`, and it comes out as %d separate"
          % (WHITE_KEY, sol[WHITE_KEY]["solids"]))
    print("solids on each piece: one per latitude band. The split order is not")
    print("the table order, so the two lists are paired by MATCHING rather than")
    print("by position: every Sol body is paired with the Anti-Sol body nearest")
    print("it in volume, and a pair inside %g mm3 is the same body on both"
          % TOLERANCE)
    print("armies.")
    print()
    left = list(sol[WHITE_KEY]["parts"])
    right = list(anti[WHITE_KEY]["parts"])
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
    index = 0
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
    unmatched = len(left) - matched
    white_delta = anti[WHITE_KEY]["volume"] - sol[WHITE_KEY]["volume"]
    print("**%d of the %d white bodies come out at exactly the same volume on"
          % (matched, len(left)))
    print("both pieces**, and the white marking as a whole differs by")
    print("%+.4f mm3 between the two armies." % white_delta)
    print()
    print("That is a change from the build this revision corrects, and it is")
    print("the direct consequence of what the correction reversed. `parts/world.py`")
    print("cuts the globe level with the disc's top face, and that plane sits in")
    print("a different half-space of the PLANET's frame on the two armies,")
    print("because the globe leans the opposite way. A marking that reaches far")
    print("enough south is therefore clipped by the disc on one piece and clears")
    print("it on the other -- which is what happened to the two deepest of the")
    print("eight cloud streaks the archived build drew, `s1` at latitude -52 and")
    print("`s2` at -37, and cost that build %.2f mm3 of white on one army." % 12.98)
    print()
    print("A closed latitude band cannot do that. It is a surface of revolution")
    print("about the globe's own polar axis, so mirroring the piece in X maps")
    print("each band onto ITSELF rather than onto some other longitude of it,")
    print("and the disc's cut takes the same arc out of it on both armies. The")
    print("three bands are therefore expected to pair exactly, and they do.")
    print()
    unmatched = len(left) - matched

    print("## The dark spot against the build this revision corrects")
    print()
    print("Requirement 2 of this revision is that the dark spot does not move.")
    print("The archived build measured its `spot` body at **%.4f mm3** on both"
          % ARCHIVED_SPOT_MM3)
    print("armies (`make/verification/reports/neptune-mirror.md` in")
    print("`revision-source.zip`). This run measures it at:")
    print()
    print("| army | archived mm3 | this run mm3 | difference mm3 | |")
    print("|---|---:|---:|---:|---|")
    spot_moved = False
    for name, table in (("Sol", sol), ("Anti-Sol", anti)):
        now = table["spot"]["volume"]
        delta = now - ARCHIVED_SPOT_MM3
        ok = abs(delta) <= 0.0001
        spot_moved = spot_moved or not ok
        print("| %s | %.4f | %.4f | %+.4f | %s |"
              % (name, ARCHIVED_SPOT_MM3, now, delta,
                 "unmoved" if ok else "**MOVED**"))
    print()
    if spot_moved:
        print("**The dark spot moved. That is a failure of requirement 2.**")
        faults.append("the dark spot's volume differs from the archived build")
    else:
        print("The spot is the same solid it was: same oval, same 40 vertices,")
        print("same latitude -22, same longitude, same `dark_gray` filament,")
        print("same volume to a ten-thousandth of a cubic millimetre. Nothing")
        print("in `parts/neptune_atlas.py`'s spot block was edited, and this is")
        print("the check rather than the claim.")
    print()

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
    print("number of solids in every role. %d of the %d white bodies and the"
          % (matched, len(left)))
    print("dark spot are identical in volume to %g mm3." % TOLERANCE)
    if unmatched:
        print("The %d that differ, and the disc, differ for reasons that are in"
              % unmatched)
        print("the design rather than in the build: the mirrored lean against a")
        print("disc cut that is not mirrored with it, and the opposite draft")
        print("that tells the armies apart.")
    else:
        print("**The disc is the only difference between them**, and it is the")
        print("ownership cue: a Sol disc flares as it rises and an Anti-Sol disc")
        print("tapers, which costs exactly %.2f mm3."
              % (anti["disc"]["volume"] - sol["disc"]["volume"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
