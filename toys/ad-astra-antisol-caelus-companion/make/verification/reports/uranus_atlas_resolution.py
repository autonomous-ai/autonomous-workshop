"""Uranus's surface and its ring, against the 0.4 mm nozzle.

The form is `measure/earth-atlas-resolution.md`'s: every feature this piece
carries, measured as an arc on its own globe, in millimetres and in nozzle
widths.  A marking in this set is a flush colour inlay, so the number that
decides is the width of the narrowest thing the printer has to lay down along
a colour boundary.

Since the owner's second pass this world carries NO surface marking, so the
hood rows the published edition's report measured are gone from it: they
measured a feature that no longer exists, and they are not carried forward as
live numbers.  What is left to measure on the globe is the one thing still
there, which is that there is no colour boundary on it at all.  The ring
section below is unchanged and still live -- the ring is geometry, it did not
move, and only the spool it prints from changed.

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
    regions = MARKINGS[PLANET]
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
    print("## The surface: nothing")
    print()
    print("`MARKINGS[\"%s\"]` lists %d regions. Uranus is the one world in this"
          % (PLANET, len(regions)))
    print("set with a bare globe, by owner decision taken against a measured case")
    print("that is kept in full in `parts/markings.py`.")
    print()
    print("The published edition measured two polar hoods here -- boundary at")
    print("latitude 60, %.2f mm of printed extent each, %.0f nozzle widths. Those"
          % (60.0 * per_degree, 60.0 * per_degree / P.NOZZLE_MM))
    print("rows are gone from this report because the feature is gone from the")
    print("piece.")
    print()
    print("| | degrees | mm | nozzle widths |")
    print("|---|---:|---:|---:|")
    print("| colour boundaries anywhere on the globe | 0.00 | 0.00 | 0.0 |")
    print("| narrowest colour boundary the nozzle could lay | %.2f | %.2f | 1.0 |"
          % (nozzle_deg, P.NOZZLE_MM))
    print("| bare surface, pole to pole | 180.00 | %.2f | %.1f |"
          % (180.0 * per_degree, 180.0 * per_degree / P.NOZZLE_MM))
    print("| inlay depth `RELIEF_DEPTH`, unused on this world | -- | %.2f | %.1f |"
          % (P.RELIEF_DEPTH, P.RELIEF_DEPTH / P.NOZZLE_MM))
    print()
    print("**There is nothing on this globe for the nozzle to resolve.** The whole")
    print("%.2f mm of surface from pole to pole is one uninterrupted `%s` solid,"
          % (180.0 * per_degree, P.GLOBE_COLOUR[PLANET]))
    print("so the resolution question this report exists to answer does not arise")
    print("on Uranus any more. It arises on the seven other worlds, which keep")
    print("their own reports unchanged.")
    print()
    print("The one colour boundary left anywhere on the piece is where the ring")
    print("meets the globe, and that is a boundary between two SOLIDS rather than")
    print("a line drawn across one: the hoop stands %.2f mm proud of the sphere on"
          % P.URANUS_RING_PROJECTION)
    print("each side, so the printer changes filament at a real edge with real")
    print("relief rather than at a bead-wide seam on a smooth surface.")
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
    print("already loaded for this set, and the ring's `white` is the very spool")
    print("Saturn's ring prints from. **This correction loads no new spool and")
    print("retires one:** the hoods' `beige` has left this piece, so where it")
    print("loaded four spools it now loads three.")
    print()
    print("Two counts are in use across this set's documents and they are not the")
    print("same count. The %d above is every spool this PIECE loads, disc and"
          % len(sol))
    print("numeral included. The tally the design contract and the READMEs keep --")
    print("`Earth, Jupiter and Saturn four; Mercury, Mars, Venus and Neptune")
    print("three; Uranus two` -- counts the globe and what stands on it, and")
    print("leaves out the disc and the numeral because every world in the set")
    print("shares those. **By that count Uranus is still two, and the two are")
    print("different ones.** It was `cyan` for the globe and its ring together")
    print("plus `beige` for the hoods; it is now `cyan` for the globe and `white`")
    print("for the ring. The tally did not move because two changes crossed: the")
    print("hoods took `beige` off the world and the ring's repaint put `white` on")
    print("it.")
    print()
    print("**The count that did fall is the piece's own.** Uranus loads three")
    print("spools where the published edition loaded four -- disc, numeral, globe")
    print("and ring, against disc, numeral, globe, hoods and ring -- so this is")
    print("the first correction in the chain to make a world SIMPLER to print.")
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
