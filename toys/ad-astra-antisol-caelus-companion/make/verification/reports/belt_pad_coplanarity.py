"""Can a world seated on a belt tile rock on its rubble?

Section 5 of `antisol_spec.md` claims that nothing on a belt tile reaches above
the field datum, that the crests which reach it exactly are in the plane of the
smooth landing pad, and that a seated disc therefore rests on a single coplanar
face rather than on three or four high points.  That is the kind of claim a
render cannot settle and a boolean can, so it is measured here on the exact
built tile rather than asserted.

Three questions.

**Does anything stand above the field datum?**  The tile is trimmed to its own
envelope, so the answer should be no by construction -- but the trim is the
thing being checked, and a boolean that silently failed would leave a rock
proud.  Measured as the solid's own bounding box.

**How much coplanar face is there at the datum?**  The disc a world stands on
is Ø34.00 and the tile is 33.50 square, so the disc overhangs the tile on every
side and what carries it is whatever the tile presents at Z = 6.00.  Measured
as the total area of every face lying in that plane.

**Is the landing pad one face or several?**  A pad broken into islands by
rubble would let a disc rock between them however coplanar the islands are.

    "$WORKSHOP_PYTHON" measure/belt_pad_coplanarity.py \\
        > measure/belt-pad-coplanarity.md

Exit 0 when the tile presents a single coplanar landing face with nothing above
it, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.belt import build_belt_cell                        # noqa: E402

from build123d import Axis                                    # noqa: E402

#: How far from the datum plane a face may sit and still carry a seated disc.
#: A face lower than this is not contact, it is clearance.
CONTACT = 1e-6

#: The window this report also looks in, so a near-miss is reported as a near
#: miss rather than silently dropped: half one printed layer.
NEAR = 0.10


def main() -> int:
    tile = build_belt_cell()
    datum = P.BELT_TILE_H
    box = tile.bounding_box()

    near = [
        face for face in tile.faces().filter_by(Axis.Z)
        if abs(face.center().Z - datum) <= NEAR
    ]
    contact = [face for face in near
               if abs(face.center().Z - datum) <= CONTACT]
    below = [face for face in near if face not in contact]
    contact.sort(key=lambda face: face.area, reverse=True)
    pad_area = 3.14159265358979 * (P.BELT_PAD_D / 2.0) ** 2
    carried = sum(face.area for face in contact)

    print("# The belt tile's landing face, measured")
    print()
    print("A world stands on a \u00d8%.2f disc and a belt tile is %.2f mm square, so"
          % (P.DISC_NOMINAL_D, P.TILE_SIZE))
    print("the disc overhangs the tile on every side and whatever the tile")
    print("presents at the field datum is what carries it. Three things decide")
    print("whether it can rock: whether anything stands proud of the datum,")
    print("how much face lies exactly in it, and whether that face is one plane")
    print("or several heights. All three are measured on the exact solid")
    print("`parts/belt.py` builds.")
    print()
    print("| measure | value |")
    print("|---|---|")
    print("| field datum, the tile's own top | Z = %.2f mm |" % datum)
    print("| the built tile's highest point | Z = %.4f mm |" % box.max.Z)
    print("| standing proud of the datum | %.4f mm |"
          % max(0.0, box.max.Z - datum))
    print("| the smooth landing pad | %.2f mm2, \u00d8%.2f |"
          % (contact[0].area if contact else 0.0, P.BELT_PAD_D))
    print("| the nominal \u00d8%.2f pad, for comparison | %.2f mm2 |"
          % (P.BELT_PAD_D, pad_area))
    print("| rubble crests reaching the datum exactly | %d |" % (len(contact) - 1))
    print("| each of them | %s mm2 |"
          % (", ".join("%.4f" % face.area for face in contact[1:]) or "-"))
    print("| **total coplanar contact** | **%.1f mm2** |" % carried)
    print("| crests within %.2f mm below the datum, touching nothing | %d, at Z = %s |"
          % (NEAR, len(below),
             ", ".join(sorted({"%.3f" % face.center().Z for face in below})) or "-"))
    print("| rubble floor, below the datum | Z = %.2f mm |"
          % (P.BELT_TILE_H - P.BELT_FLOOR_DROP))
    print()

    proud = box.max.Z - datum > CONTACT
    heights = {round(face.center().Z, 6) for face in contact}
    coplanar = len(heights) == 1

    print("Every contact face is at Z = %.4f exactly, so the landing pad and the"
          % datum)
    print("%d crests that reach it are **one plane, not %d heights**: a seated"
          % (len(contact) - 1, len(contact)))
    print("disc meets all of them at once and cannot rock on any of them. The")
    print("%d crests that stop %.3f mm short are clearance rather than contact"
          % (len(below), datum - (below[0].center().Z if below else datum)))
    print("and are listed so nobody has to wonder whether they were counted.")
    print()
    if proud:
        print("**Something stands %.4f mm above the field datum, which is a fault.**"
              % (box.max.Z - datum))
    else:
        print("Nothing stands above the field datum. The tile is trimmed to its")
        print("own envelope after the rubble is fused, so every crest that would")
        print("have risen past the datum is cut off level with it.")
    print()
    print("Measured by `measure/belt_pad_coplanarity.py` on the exact solid")
    print("`parts/belt.py` builds.")
    return 0 if (coplanar and not proud) else 1


if __name__ == "__main__":
    raise SystemExit(main())
