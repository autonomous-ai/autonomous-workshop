"""Does a world seated on a star or in a corona well foul the flames or tongues?

A reader of the state sheet at board scale sees a flame and a seated world
overlap in projection and cannot tell whether they touch -- an independent
critic of this build read exactly that and reported a cone passing through a
sphere.  A render cannot answer it; a boolean can.

This places every one of the eight worlds at the two exact heights the assembly
gives it -- the corona well a captured world drops into, and the star cell a
winning world walks onto -- beside the exact star and corona solids, and
measures the volume the two solids share.  The seats are imported from
`assemblies.product` rather than restated, so this cannot drift from what the
set actually builds.

    "$WORKSHOP_PYTHON" measure/seated_clearance.py > measure/seated-piece-clearance.md

Exit 0 when nothing shares volume, 1 when anything does.
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
from parts.world import build_world                           # noqa: E402

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
    star = den_bodies()
    star_solids = [
        Location((0, 0, POCKET_FLOOR)) * star[role] for role in ("star", "flare")
    ]

    print("# A seated world against the star and the corona tongues")
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
    print("| world | globe Ømm | in a corona well mm3 | on a star mm3 |")
    print("|---|---|---|---|")
    failures = []
    for planet in P.PLANETS:
        piece = build_world(planet, "sol")
        in_well = shared(Location((0, 0, CORONA_SEAT)) * piece, corona)
        on_star = max(
            shared(Location((0, 0, DEN_SEAT)) * piece, solid)
            for solid in star_solids
        )
        print("| %s | %.2f | %.6f | %.6f |"
              % (planet, P.globe_diameter(planet), in_well, on_star))
        for where, value in (("a corona well", in_well), ("a star", on_star)):
            if value > NOISE_MM3:
                failures.append(
                    "%s standing on %s shares %.4f mm3 with it"
                    % (planet, where, value))
    print()
    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- %s" % item)
    else:
        print("Nothing shares volume with anything. A captured world drops into")
        print("a corona well without touching either of that tile's raised")
        print("tongues, and a winning world stands on a star without touching")
        print("either of its flames, on all eight worlds -- including Jupiter,")
        print("the widest globe in the set. What a board-scale render shows at")
        print("these cells is two parts overlapping in projection, not in space.")
    print()
    print("Measured by `measure/seated_clearance.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
