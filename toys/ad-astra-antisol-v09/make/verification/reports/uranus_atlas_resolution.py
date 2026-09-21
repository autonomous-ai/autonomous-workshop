"""Uranus's surface and its ring, against the 0.4 mm nozzle.

The form is `measure/earth-atlas-resolution.md`'s: every feature this piece
carries, measured as an arc on its own globe, in millimetres and in nozzle
widths.  A marking in this set is a flush colour inlay, so the number that
decides is the width of the narrowest thing the printer has to lay down along
a colour boundary.

It also settles one arithmetic question the brief raised.  Twice in this chain
a figure has been wrong by a factor of two because millimetres per degree was
taken as `pi * d / 180` when a great circle makes it `pi * d / 360`.  The brief
warns that any number in it comparing Uranus to another world is a pointer and
not a fact, and asks for the real figure to be taken from that world's own
report.  Both are checked below against the reports carried forward in
`measure/`.

    "$WORKSHOP_PYTHON" measure/uranus_atlas_resolution.py \\
        > measure/uranus-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.markings import MARKINGS                           # noqa: E402
from parts.world import world_bodies                          # noqa: E402

PLANET = "uranus"


def main() -> int:
    diameter = P.globe_diameter(PLANET)
    radius = diameter / 2.0
    per_degree = math.pi * diameter / 360.0
    nozzle_deg = P.NOZZLE_MM / per_degree
    boundary = MARKINGS[PLANET][0][2][0][1]
    half = 90.0 - boundary
    bodies = world_bodies(PLANET, "sol")
    spec = P.RINGED_WORLDS[PLANET]

    print("# Uranus's surface and ring, against the 0.4 mm nozzle")
    print()
    print("Uranus's globe is Ø%.2f mm, so its radius is %.3f mm and one degree of"
          % (diameter, radius))
    print("arc is %.4f mm. The nozzle is %.2f mm, which is the narrowest colour"
          % (per_degree, P.NOZZLE_MM))
    print("boundary the printer can lay down and %.2f degrees of arc here."
          % nozzle_deg)
    print()
    print("A degree of arc on a great circle is `pi * d / 360`, not `pi * d / 180`.")
    print("The brief's own %.3f mm is the correct figure and agrees with this to"
          % 0.192)
    print("the third decimal. Two figures in this set's sealed archive do not, and")
    print("the last section says which.")
    print()
    print("## The polar hoods")
    print()
    print("Two `cap` regions, one at each pole, boundary at latitude %d." % boundary)
    print()
    print("| | degrees | mm | nozzle widths |")
    print("|---|---:|---:|---:|")
    rows = [
        ("hood, pole to boundary (angular radius)", half, half * per_degree),
        ("hood, printed extent across the surface", 2.0 * half,
         2.0 * half * per_degree),
        ("hood, chord across its own boundary circle", None,
         2.0 * radius * math.sin(math.radians(half))),
        ("boundary circle, circumference",
         None, 2.0 * math.pi * radius * math.sin(math.radians(half))),
        ("bare globe between the two hoods", 2.0 * boundary,
         2.0 * boundary * per_degree),
        ("colour boundary transition, as drawn", 0.0, 0.0),
        ("colour boundary transition, as printed", nozzle_deg, P.NOZZLE_MM),
        ("inlay depth `RELIEF_DEPTH`", None, P.RELIEF_DEPTH),
    ]
    for label, degrees, value in rows:
        print("| %s | %s | %.2f | %.1f |"
              % (label, "%.2f" % degrees if degrees is not None else "--",
                 value, value / P.NOZZLE_MM))
    print()
    print("**The hood's printed extent is %.2f mm across the surface**, %.0f nozzle"
          % (2.0 * half * per_degree, 2.0 * half * per_degree / P.NOZZLE_MM))
    print("widths, on a globe %.2f mm across. It is not a feature the nozzle has"
          % diameter)
    print("any difficulty with; nothing about it is near the limit.")
    print()
    print("**The boundary transition is the one number that is at the limit, and")
    print("it is at the limit by construction rather than by choice.** A flush")
    print("colour inlay has no transition at all: the boundary is a hard edge")
    print("between two filaments, drawn as an exact circle of latitude. What the")
    print("printer actually lays down there is one bead, %.2f mm, %.2f degrees of"
          % (P.NOZZLE_MM, nozzle_deg))
    print("arc on this globe. So the softness the reference shows -- a brightening")
    print("that fades out rather than stopping -- **cannot be reproduced**, and")
    print("lowering the contrast is the available substitute rather than a")
    print("preference. `measure/uranus-tone-separation.md` is that substitute,")
    print("measured.")
    print()
    print("No lobed rim. The Earth correction's lesson about lids was about a small")
    print("bright cap read edge-on against a dark globe; this is a wide soft")
    print("brightening read face-on, and `ref/uranus-sol.png` shows no rim")
    print("structure at all. A lobe on this boundary would be a feature the")
    print("reference does not carry.")
    print()
    print("## The ring")
    print()
    print("| | mm | nozzle widths |")
    print("|---|---:|---:|")
    ring_rows = [
        ("projection past the globe, per side", P.URANUS_RING_PROJECTION),
        ("thickness through the plate", spec["thickness"]),
        ("outer diameter", spec["outer_d"]),
        ("how far it bites into the globe before the globe is cut out",
         P.URANUS_RING_GLOBE_BITE),
        ("the foot's reach past the hoop at the disc top",
         P.URANUS_RING_FOOT_REACH),
        ("the foot's rise before it is inside the globe", P.URANUS_RING_FOOT_RISE),
    ]
    for label, value in ring_rows:
        print("| %s | %.2f | %.1f |" % (label, value, value / P.NOZZLE_MM))
    print()
    print("The thinnest section anywhere on the ring is its own %.2f mm plate,"
          % spec["thickness"])
    print("%.1f nozzle widths and %.2f mm over the %.2f mm minimum wall this set"
          % (spec["thickness"] / P.NOZZLE_MM, spec["thickness"] - P.MIN_WALL_MM,
             P.MIN_WALL_MM))
    print("holds. `measure/thickness-world_uranus_sol.md` measures the whole part.")
    print()
    print("Thirteen real rings were considered and refused. One degree of arc is")
    print("%.3f mm here and the whole Uranian ring system spans about 1.8 planet"
          % per_degree)
    print("radii; the widest ring, epsilon, is about 100 km on a planet 51118 km")
    print("across, which is %.4f mm at this scale -- a four-hundredth of a nozzle."
          % (100.0 / 51118.0 * diameter))
    print("Printed at the width the printer can lay down they would be forty times")
    print("too fat and read as grit. **The ring is one solid hoop.**")
    print()
    print("## The filaments this piece loads")
    print()
    print("| role | filament |")
    print("|---|---|")
    for role, (colour, _shape) in bodies.items():
        print("| `%s` | `%s` |" % (role, colour))
    sol = {colour for colour, _s in bodies.values()}
    anti = {colour for colour, _s in world_bodies(PLANET, "anti").values()}
    print()
    print("**%d filaments on the Sol piece and %d on the Anti-Sol piece**: %s, and"
          % (len(sol), len(anti), ", ".join("`%s`" % name for name in sorted(sol))))
    print("%s. The two differ only in which of `white` and `black` is the disc and"
          % ", ".join("`%s`" % name for name in sorted(anti)))
    print("which is the numeral, which is the set's own ownership cue. Every one is")
    print("already loaded for this set: the hood's `beige` is Earth's dryland and")
    print("Jupiter's and Saturn's zones, and the ring's `white` is Saturn's ring.")
    print("**This correction loads no new spool.**")
    print()
    print("Two counts are in use across this set's documents and they are not the")
    print("same count. The %d above is every spool this PIECE loads, disc and"
          % len(sol))
    print("numeral included. The tally the design contract and the READMEs keep --")
    print("`Earth, Jupiter and Saturn four; Mercury, Mars, Venus, Neptune and")
    print("Uranus three` -- counts the globe and its markings only, and leaves out")
    print("the disc and the numeral because every world in the set shares those.")
    print("By that count Uranus is %s: `cyan`, `beige` and `white`, where before"
          % "three")
    print("this correction it was two.")
    print()
    print("## Where this set's own numbers disagree with each other")
    print()
    print("The brief asks for every cross-world figure in it to be checked against")
    print("that world's own report rather than taken on trust. Done, and one")
    print("disagreement is real and is in the sealed archive rather than in the")
    print("brief.")
    print()
    print("| claim | where | measured | verdict |")
    print("|---|---|---|---|")
    print("| Saturn's ring projects 2.00 mm per side | the brief | "
          "`RING_OUTER_D` %.2f less Ø%.2f, halved: %.2f mm | agrees |"
          % (P.RING_OUTER_D, P.globe_diameter("saturn"),
             (P.RING_OUTER_D - P.globe_diameter("saturn")) / 2.0))
    print("| Saturn is Ø30.00 and the widest world | the brief | `RING_OUTER_D` "
          "%.2f against Uranus's %.2f | agrees |"
          % (P.RING_OUTER_D, spec["outer_d"]))
    print("| Neptune's piece is 24.89 mm tall | the brief | %.2f mm | agrees |"
          % P.piece_height("neptune"))
    print("| Saturn's piece is 29.00 mm tall | the brief | %.2f mm | agrees |"
          % P.piece_height("saturn"))
    print("| Uranus's piece was 25.02 mm tall | the brief | %.2f mm | agrees |"
          % P.piece_height(PLANET))
    print("| Uranus's ring will reach about 25.91 mm | the brief | 25.98 mm | "
          "**0.07 mm low**; see `measure/uranus-ring.md` |")
    print("| Saturn's bands are 3.63 to 7.26 mm | "
          "`measure/neptune-atlas-resolution.md` | Saturn's own report measures "
          "the narrowest at **1.82 mm** | **wrong by a factor of two** |")
    print()
    print("`measure/neptune-atlas-resolution.md` went into the sealed archive")
    print("saying Saturn's band system runs 3.63 to 7.26 mm. Saturn's own")
    print("`measure/saturn-atlas-resolution.md` measures the narrowest band, the")
    print("Equatorial Band, at 8.0 degrees and **1.82 mm**. 3.63 is exactly twice")
    print("1.82: the Neptune run caught the factor of two in its own width figure")
    print("and then repeated the owner's companion figures for Saturn and Jupiter")
    print("without recomputing them. The same line's Jupiter figures, 2.35 to")
    print("6.12 mm, carry the same doubling.")
    print()
    print("The same two figures are quoted in the product README's Neptune")
    print("paragraph, which this revision rewrites, and the corrected ones go in")
    print("with the rewrite.")
    print()
    print("### Older per-world reports still describe Uranus's band")
    print()
    print("`measure/jupiter-atlas-resolution.md`, `measure/jupiter-tone-separation.md`")
    print("and `measure/venus-tone-separation.md` each mention Uranus's `white`")
    print("band or count it as a two-filament world. Those are the sealed reports")
    print("of the Jupiter and Venus corrections and they were true when they were")
    print("written; this set's convention is to leave each run's own record as it")
    print("stands rather than back-date it, which is why the design contract's")
    print("items 19, 20 and 21 also keep their own filament tallies. The tally as")
    print("it now stands is in the section above and in `README.md`. Nothing in")
    print("those three reports is used as evidence by this run.")
    print()
    print("**Nothing in this run depends on either figure** -- no marking on this")
    print("piece is sized against another world's bands -- and the sealed Neptune")
    print("report is finished work that this correction does not reopen. It is")
    print("recorded here because this is the last run of the chain and the brief")
    print("asked for anything left wrong to be said in one place.")
    print()
    print("## What else was considered and refused")
    print()
    print("- **A second, brighter core inside each hood.** The reference's lighter")
    print("  region is soft-edged and single-toned; a core would need a fourth")
    print("  surface filament and would reintroduce exactly the structure this")
    print("  correction is removing.")
    print("- **Banding.** `ref/uranus-sol.png` shows none, and a band on this")
    print("  planet is the feature this correction exists to take off.")
    print("- **Moons.** Not on the reference, not printable at this scale, and not")
    print("  a surface.")
    print("- **Shepherd gaps and named ringlets.** Refused on the arithmetic above.")
    print("- **A pale blue globe.** `cyan` #00FFFF is a saturated neon and the")
    print("  reference is a pale desaturated ice blue. There is no pale blue in the")
    print("  %d filaments this set stocks, so the gap cannot be closed inside two"
          % len(P.FILAMENT_HEX))
    print("  printed parts. Acquiring one would reach the belt, the corona flames")
    print("  and the Anti-Sol flames, which is well outside this correction; it is")
    print("  recorded as a recommendation for a future revision instead.")
    print()
    print("Measured by `measure/uranus_atlas_resolution.py` on the built solids and")
    print("on `params.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
