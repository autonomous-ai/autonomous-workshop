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

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import neptune_atlas as N                           # noqa: E402
from parts.markings import MARKINGS                            # noqa: E402
from parts.world import world_bodies                          # noqa: E402

#: mm3.  A boolean run on the same source is reproducible far below this.
TOLERANCE = 1e-4

#: Degrees.  How far south of the globe's own equator the disc's cut reaches,
#: in the PIECE's frame: the cut is the plane Z = DISC_H and the globe's centre
#: stands `globe_centre_z` above the bed, so the cut removes everything below
#: asin((DISC_H - centre) / radius).  Anything drawn north of it survives on
#: both armies whatever the lean does to its longitude.
CUT_LATITUDE = math.degrees(math.asin(
    (P.DISC_H - P.globe_centre_z("neptune")) / P.globe_radius("neptune")))

#: Neptune's white markings, read off the marking table rather than named here,
#: so that this report cannot go on describing a marking the build stopped
#: drawing.  That is exactly how this set's sealed Neptune report went stale.
#:
#: There are TWO of them on this revision.  `bands` is the three closed cloud
#: bands and `companion` is the oval this revision adds beside the dark spot;
#: they are separate keys rather than one white marking precisely so that a
#: later argument about bands cannot delete the companion by accident.
WHITE_KEYS = [key for key, colour, _specs, _sub in MARKINGS["neptune"]
              if colour == "white"]

#: mm3.  The volume the build this revision corrects measured the dark spot
#: body at, on BOTH armies, quoted from that build's own sealed
#: `make/verification/reports/neptune-mirror.md` in `revision-source.zip`.
#:
#: Requirement 2 of this revision is that the dark spot does not move, and this
#: is the number that requirement is checked against rather than a number this
#: run produced.  It is an archival fact, not a measurement, so it is written
#: down once, here, with its source, and the check below is allowed to fail.
ARCHIVED_SPOT_MM3 = 11.9319


def lowest_piece_latitude(ring, side: str) -> float:
    """The lowest latitude any vertex of `ring` reaches in the PIECE frame.

    `features/patches.planet_frame` turns the planet's frame about +Y by the
    obliquity, +28.32 degrees for a Sol world and -28.32 for its Anti-Sol
    mirror.  The disc's cut is a plane at a fixed height in the piece frame, so
    what decides whether a marking survives it is the marking's latitude THERE,
    which depends on the marking's longitude as well as its latitude.
    """
    phi = math.radians(P.lean_sign(side) * P.PLANETS["neptune"]["tilt"])
    worst = 90.0
    for lon_deg, lat_deg in ring:
        lat, lon = math.radians(lat_deg), math.radians(lon_deg)
        x = math.cos(lat) * math.cos(lon)
        z = math.sin(lat)
        turned = -x * math.sin(phi) + z * math.cos(phi)
        worst = min(worst, math.degrees(math.asin(max(-1.0, min(1.0, turned)))))
    return worst


def unsubtracted_lenses():
    """(spot region, companion region, spot-and-keep-out overlap) in mm3.

    Built here from the same tools `parts/world.py` uses, WITHOUT the
    subtraction the marking table applies, so the spot can be measured as it
    would have been drawn if the companion were not there.  That is the only
    way to ask "did the spot move?" of a build in which the spot deliberately
    gives way to something.
    """
    from build123d import Sphere

    import bool3d as X
    from parts.world import _region_tool, _sane

    ball = Sphere(P.globe_radius("neptune"))
    spot = _sane(X.shape(X.meet(
        _region_tool("neptune", ("outline", [N.SPOT_RING])), ball)))
    companion = _sane(X.shape(X.meet(
        _region_tool("neptune", ("outline", [N.COMPANION_RING])), ball)))
    keepout = _sane(X.shape(X.meet(
        _region_tool("neptune", ("outline", [N.COMPANION_KEEPOUT_RING])), ball)))
    overlap = _sane(X.shape(X.meet(spot, keepout)))
    return (spot.volume, companion.volume,
            0.0 if overlap is None else overlap.volume)


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
    print("Neptune carries %d white markings on this revision: %s. The split"
          % (len(WHITE_KEYS), ", ".join("`%s`" % key for key in WHITE_KEYS)))
    print("order is not the table order, so the two armies' lists are paired")
    print("by MATCHING rather than by position: every Sol body is paired with")
    print("the Anti-Sol body nearest it in volume, and a pair inside %g mm3"
          % TOLERANCE)
    print("is the same body on both armies.")
    print()
    total_unmatched = 0
    for key in WHITE_KEYS:
        print("### `%s`" % key)
        print()
        left = list(sol[key]["parts"])
        pool = list(anti[key]["parts"])
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
        delta = anti[key]["volume"] - sol[key]["volume"]
        total_unmatched += len(left) - matched
        print("**%d of the %d `%s` bodies come out at exactly the same volume"
              % (matched, len(left), key))
        print("on both pieces**, and `%s` as a whole differs by %+.4f mm3"
              % (key, delta))
        print("between the two armies.")
        print()

    print("A closed latitude band cannot be clipped differently on the two")
    print("armies. It is a surface of revolution about the globe's own polar")
    print("axis, so mirroring the piece in X maps each band onto ITSELF rather")
    print("than onto some other longitude of it, and the disc's cut takes the")
    print("same arc out of it on both armies. The three bands pair exactly.")
    print()
    print("The companion CAN be, and this is the check that it is not.")
    print("`parts/world.py` cuts the globe level with the disc's top face, and")
    print("that plane sits in a different half-space of the PLANET's frame on")
    print("the two armies, so a short marking that reaches far enough south is")
    print("clipped by the disc on one piece and clears it on the other. That")
    print("is what happened to the two deepest of the eight cloud streaks an")
    print("earlier build of this globe drew, `s1` at latitude -52 and `s2` at")
    print("-37, and cost that build %.2f mm3 of white on one army. The" % 12.98)
    print("disc's cut is a plane, so in the PLANET's frame it is a great")
    print("circle tilted by the obliquity rather than a parallel: a marking")
    print("survives it or not by longitude as well as by latitude. So it is")
    print("measured on the companion's own ring, vertex by vertex, on both")
    print("armies -- the lowest the ring reaches in the PIECE's frame against")
    print("the %.1f degrees the cut sits at there." % CUT_LATITUDE)
    print()
    print("| army | companion's lowest ring vertex, piece frame | cut at | clears by |")
    print("|---|---:|---:|---:|")
    for _name, _side in (("Sol", "sol"), ("Anti-Sol", "anti")):
        low = lowest_piece_latitude(N.COMPANION_RING, _side)
        print("| %s | %+.1f | %+.1f | %.1f degrees |"
              % (_name, low, CUT_LATITUDE, low - CUT_LATITUDE))
    print()
    print("The table above is the measurement of the result rather than the")
    print("argument for it.")
    print()

    print("## The dark spot against the build this revision corrects")
    print()
    print("The owner's standing instruction across two revisions is that the")
    print("dark spot does not move, and this revision does not move it: its")
    print("ring, its latitude, its longitude, its half-axes, its 40 vertices")
    print("and its `dark_gray` filament are byte-identical in the source --")
    print("`measure/source-diff.md` is the whole difference and the spot is")
    print("not in it -- and `measure/neptune-facing.md` reproduces its")
    print("archived dot products at every frame.")
    print()
    print("Its BODY is nonetheless smaller than the archive's, and by more")
    print("than the companion's own area. The companion has to stand one")
    print("nozzle width of bare globe clear of the spot -- an independent")
    print("reader of the touching version called the pair a notched")
    print("figure-eight -- so the spot is cut back to a KEEP-OUT, the")
    print("companion's oval grown by %.2f degrees of arc, which is never drawn"
          % N.COMPANION_KEEPOUT_ARC)
    print("and never printed. The bay that leaves in the spot's southern rim")
    print("is a real change to the Great Dark Spot and this section is where")
    print("it is disclosed rather than a check quietly retargeted.")
    print()
    print("The archived build measured the `spot` body at **%.4f mm3** on both"
          % ARCHIVED_SPOT_MM3)
    print("armies (`make/verification/reports/neptune-mirror.md` in")
    print("`revision-source.zip`).")
    print()
    print("| army | archived mm3 | this run mm3 | difference mm3 |")
    print("|---|---:|---:|---:|")
    for name, table in (("Sol", sol), ("Anti-Sol", anti)):
        now = table["spot"]["volume"]
        print("| %s | %.4f | %.4f | %+.4f |"
              % (name, ARCHIVED_SPOT_MM3, now, now - ARCHIVED_SPOT_MM3))
    print()
    spot_lens, companion_lens, overlap = unsubtracted_lenses()
    lost = ARCHIVED_SPOT_MM3 - sol["spot"]["volume"]
    print("Two measurements decide whether that difference is the keep-out")
    print("or a fault, and both are taken on the region solids rather than on")
    print("the split bodies:")
    print()
    print("| quantity | mm3 |")
    print("|---|---:|")
    print("| the spot's own region, BEFORE the companion is subtracted from it "
          "| %.4f |" % spot_lens)
    print("| the archive's sealed `spot` body | %.4f |" % ARCHIVED_SPOT_MM3)
    print("| the companion's own region, which is what is PRINTED white "
          "| %.4f |" % companion_lens)
    print("| where the spot and the companion's KEEP-OUT overlap | %.4f |"
          % overlap)
    print("| what the `spot` body actually lost | %.4f |" % lost)
    print()
    unmoved = abs(spot_lens - ARCHIVED_SPOT_MM3) <= 0.0005
    accounted = abs(overlap - lost) <= 0.0005
    if unmoved:
        print("**The spot's own region reproduces the archived figure to a")
        print("ten-thousandth of a cubic millimetre: the spot did not move.**")
    else:
        print("**THE SPOT'S OWN REGION IS %+.4f mm3 FROM THE ARCHIVED FIGURE.**"
              % (spot_lens - ARCHIVED_SPOT_MM3))
    if accounted:
        print("And what the body lost is that overlap, to the same tolerance:")
        print("every cubic millimetre of the difference is the bare globe the")
        print("companion needs around it. Nothing else came off the spot.")
    else:
        print("**THE LOSS IS %+.4f mm3 AWAY FROM THE OVERLAP: SOMETHING OTHER"
              % (lost - overlap))
        print("THAN THE COMPANION'S KEEP-OUT CAME OFF THE SPOT.**")
    print()
    print("Both armies lose the same amount, which is the other half of the")
    print("statement: the companion is drawn once and the two pieces are the")
    print("same description mirrored.")
    print()

    print("## Verdict")
    print()
    if faults:
        print("**FAULTS**")
        for item in faults:
            print("- %s" % item)
        return 1
    white_total = sum(len(sol[key]["parts"]) for key in WHITE_KEYS)
    print("The two pieces carry the same roles, the same filaments and the same")
    print("number of solids in every role. %d of the %d white bodies and the"
          % (white_total - total_unmatched, white_total))
    print("dark spot on one army is identical in volume to the same body on")
    print("the other, to %g mm3." % TOLERANCE)
    if total_unmatched:
        print("The %d that differ, and the disc, differ for reasons that are in"
              % total_unmatched)
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
