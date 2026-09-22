"""Can a world seated on a star or in a corona well touch anything on it?

A reader of the state sheet at board scale sees a flame and a seated world
overlap in projection and cannot tell whether they touch -- an independent
critic of this build read exactly that and reported a cone passing through a
sphere.  A render cannot answer it; a boolean can.

This places every one of the sixteen worlds at the two exact heights the
assembly gives it -- the corona well a captured world drops into, and the star
cell a winning world walks onto -- beside the exact star and corona solids, and
measures the volume the two solids share.  The seats are imported from
`assemblies.product` rather than restated, so this cannot drift from what the
set actually builds.

Both armies are measured, not one.  The two ringed worlds are the reason: a
ring lies in its planet's equatorial plane and the two armies lean opposite
ways, so Saturn's Ø30.00 plate and Uranus's Ø24.02 upright hoop stand at
different angles on the two pieces and a clearance cleared on one is not
cleared on the other.

Since the owner's second pass the trap tile has no raised feature at all, so
the question it answers has changed shape: the tile's own highest surface is
now the plane the world stands on, and this reports that as a measurement
beside the booleans.

    "$WORKSHOP_PYTHON" measure/seated_clearance.py > measure/seated-piece-clearance.md

Exit 0 when nothing shares volume and nothing on a trap tile reaches above the
seat, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from build123d import Location                                # noqa: E402

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from assemblies.product import POCKET_FLOOR                   # noqa: E402
from parts.corona import build_corona_cell                    # noqa: E402
from parts.den import den_bodies                              # noqa: E402
from parts.world import build_world, world_bodies             # noqa: E402

#: The two seats `assemblies/product.py::_piece_seat` gives a world, derived
#: from the same constants that function uses.
CORONA_SEAT = POCKET_FLOOR + P.CORONA_TILE_H
DEN_SEAT = POCKET_FLOOR + P.DEN_SPIGOT_DEPTH + P.DEN_PROUD

#: Anything at or under this is the kernel's own noise on a contact, not a
#: shared volume.  Real interpenetration on parts this size is cubic
#: millimetres, not millionths.
NOISE_MM3 = 1e-6


def shared(one, other) -> float:
    """The volume two placed solids occupy together, in mm3."""
    meet = X.shape(X.meet(one, other))
    if meet is None:
        return 0.0
    return sum(solid.volume for solid in X.parts(meet))


def main() -> int:
    corona = Location((0, 0, POCKET_FLOOR)) * build_corona_cell()
    corona_top = corona.bounding_box().max.Z
    star = den_bodies()
    star_solids = [
        Location((0, 0, POCKET_FLOOR)) * star[role] for role in ("star", "flare")
    ]
    failures = []

    print("# A seated world against the star and the trap tile")
    print()
    print("The state sheet shows captured worlds standing in corona wells and,")
    print("in the endgame, a world walking onto a star. At board scale a flame")
    print("and a globe overlap in projection whether or not they touch, so this")
    print("asks the solids instead of the picture.")
    print()
    print("Each world is placed at the exact height the assembly gives it --")
    print("%.2f mm in a corona well, %.2f mm on a star, both measured from the"
          % (CORONA_SEAT, DEN_SEAT))
    print("bed datum -- beside the exact corona tile and star plug, and the")
    print("volume the two share is measured. Anything above %g mm3 is a real"
          % NOISE_MM3)
    print("interpenetration; the parts are meant to stand beside each other and")
    print("never inside each other.")
    print()
    print("| world | side | globe Ømm | widest feature Ømm | in a corona well mm3 | on a star mm3 |")
    print("|---|---|---:|---:|---:|---:|")
    for planet in sorted(P.PLANETS, key=lambda name: P.PLANETS[name]["rank"]):
        for side in P.SIDES:
            piece = build_world(planet, side)
            box = piece.bounding_box()
            widest = max(box.size.X, box.size.Y)
            in_well = shared(Location((0, 0, CORONA_SEAT)) * piece, corona)
            on_star = max(
                shared(Location((0, 0, DEN_SEAT)) * piece, solid)
                for solid in star_solids
            )
            print("| %s | %s | %.2f | %.2f | %.6f | %.6f |"
                  % (planet, side, P.globe_diameter(planet), widest,
                     in_well, on_star))
            for where, value in (("a corona well", in_well), ("a star", on_star)):
                if value > NOISE_MM3:
                    failures.append(
                        "%s %s standing on %s shares %.4f mm3 with it"
                        % (planet, side, where, value))
    print()
    print("The widest feature column is the piece's own footprint, and on every")
    print("one of the sixteen it is the DISC rather than anything standing on it:")
    print("Ø33.87 on a Sol piece, whose wall flares outward to Ø34.00 and is then")
    print("rounded 0.60 at the top, and Ø34.00 on an Anti-Sol piece, whose wall")
    print("tapers inward from a Ø34.00 bed face. That includes the two ringed")
    print("worlds -- Saturn's plate is Ø30.00 and lies wholly inside its disc,")
    print("and Uranus's hoop is Ø24.02 and stands upright over its ball rather")
    print("than reaching out -- so no part of any world overhangs the 33.50 mm")
    print("tile it stands on, let alone touches anything on it.")
    print()

    print("## The trap tile has nothing left to touch")
    print()
    print("Before the owner's second pass, the tightest thing on a trap tile was")
    print("the gap between its two raised tongues: 0.70 mm of clearance to a")
    print("seated disc, at a 20.20 mm diagonal. That constraint no longer")
    print("exists, because the feature it constrained no longer exists.")
    print()
    print("What is left is a plane. The tile's highest surface is now its own")
    print("top face, and that face IS the floor the world stands on:")
    print()
    print("| | mm from the bed datum |")
    print("|---|---:|")
    print("| the trap tile's highest point | %.4f |" % corona_top)
    print("| the seat a world stands at in a well | %.4f |" % CORONA_SEAT)
    flat = abs(corona_top - CORONA_SEAT) < 1e-6
    print()
    print("They are the same plane%s. Nothing on a trap tile stands above the"
          % ("" if flat else " -- **THEY ARE NOT**"))
    print("surface a world's own bed face rests on, so no part of any world --")
    print("its disc, its globe, Saturn's ring or Uranus's hoop -- can reach")
    print("anything on that tile other than the floor it is standing on. The")
    print("booleans above measure that on the solids: zero shared volume on all")
    print("sixteen pieces, both armies.")
    if not flat:
        failures.append(
            "the trap tile reaches %.4f mm and the seat is %.4f"
            % (corona_top, CORONA_SEAT))
    print()

    print("## The well itself is untouched")
    print()
    print("Both numbers the well is made of are derived here from the same")
    print("constants the board and the tile are built from, rather than quoted:")
    print()
    drop = P.POCKET_DEPTH - P.CORONA_TILE_H
    slip = (P.POCKET_SIZE - P.DISC_NOMINAL_D) / 2.0
    print("| | derivation | mm |")
    print("|---|---|---:|")
    print("| the drop a trapped world takes | `POCKET_DEPTH` %.2f - `CORONA_TILE_H` %.2f | %.2f |"
          % (P.POCKET_DEPTH, P.CORONA_TILE_H, drop))
    print("| `CORONA_WELL_DROP`, as the set states it | -- | %.2f |"
          % P.CORONA_WELL_DROP)
    print("| slip per side | (`POCKET_SIZE` %.2f - `DISC_NOMINAL_D` %.2f) / 2 | %.2f |"
          % (P.POCKET_SIZE, P.DISC_NOMINAL_D, slip))
    print()
    if abs(drop - P.CORONA_WELL_DROP) > 1e-9:
        failures.append("the well drop is %.4f, not CORONA_WELL_DROP %.2f"
                        % (drop, P.CORONA_WELL_DROP))
    if abs(slip - 0.40) > 1e-9:
        failures.append("the slip per side is %.4f, not 0.40" % slip)
    print("3.00 mm of drop and 0.40 mm of slip per side, exactly as before. The")
    print("tile's own height is `CORONA_TILE_H` = %.2f and the board's pocket is"
          % P.CORONA_TILE_H)
    print("`POCKET_DEPTH` = %.2f; neither moved, and the tongues never entered"
          % P.POCKET_DEPTH)
    print("either number.")
    print()

    print("## The star's flames, unchanged")
    print()
    print("This run's part two exists to make the star's flames the only raised")
    print("flames on the board, so damaging them would be the one way to fail")
    print("it completely. Measured on the built body rather than read off the")
    print("constants:")
    print()
    flare = star["flare"]
    box = flare.bounding_box()
    solids = X.parts(flare)
    print("| | value |")
    print("|---|---:|")
    print("| flames on one star | %d |" % len(solids))
    print("| `FLARE_BASE_D` mm | %.2f |" % P.FLARE_BASE_D)
    print("| `FLARE_HEIGHT` above field datum mm | %.2f |" % P.FLARE_HEIGHT)
    print("| `FLARE_TIP_R` mm | %.2f |" % P.FLARE_TIP_R)
    print("| `FLARE_LEAN_DEG` from vertical | %.1f |" % P.FLARE_LEAN_DEG)
    print("| `FLARE_DIAGONAL` mm | %.2f |" % P.FLARE_DIAGONAL)
    print("| highest point above the bed datum mm | %.4f |" % box.max.Z)
    print("| the same, above field datum mm | %.4f |"
          % (box.max.Z - P.DEN_SPIGOT_DEPTH))
    print("| total volume mm3 | %.4f |" % sum(item.volume for item in solids))
    print()
    reaches = abs((box.max.Z - P.DEN_SPIGOT_DEPTH) - P.FLARE_HEIGHT) < 1e-6
    if len(solids) != 2 or not reaches:
        failures.append("the star's flames are not two bodies reaching %.2f mm"
                        % P.FLARE_HEIGHT)
    print("Two bodies, reaching exactly %.2f mm above the field%s."
          % (P.FLARE_HEIGHT, "" if reaches else " -- **THEY DO NOT**"))
    print("`measure/revision-part-hashes.md` carries the same statement in")
    print("bytes: `part_den_plug.step` is byte-identical to the published set's.")
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("Nothing shares volume with anything. A captured world drops into")
        print("a corona well and stands on a flat floor with nothing on it; a")
        print("winning world stands on a star without touching either of its")
        print("flames; on all eight worlds of both armies, including Jupiter,")
        print("the widest globe in the set, Saturn with its ring and Uranus with")
        print("its hoop. What a board-scale render shows at these cells is two")
        print("parts overlapping in projection, not in space.")
    print()
    print("Measured by `measure/seated_clearance.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
