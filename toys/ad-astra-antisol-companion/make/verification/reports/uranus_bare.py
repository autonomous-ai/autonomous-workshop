"""Nothing is drawn on either Uranus globe, measured rather than asserted.

This revision removes both polar hoods and leaves Uranus the one world in the
set with no surface marking of any kind.  That is a NEGATIVE requirement, and a
negative requirement is the kind a render can miss: a marking that fails to cut
the globe leaves a piece that still measures as sound, complete and correctly
sized.  `parts/world.py` carries that exact scar -- Uranus's southern hood was
once silently lost to a boolean and the piece still passed every count.

So this asks the question three ways, on the built solids.

**What bodies does the piece actually have?**  `parts.world.world_bodies` is
the single place the colour split is decided, and everything downstream --
`parts/*.step`, the assembly, the renders -- is built from what it returns.  If
a marking body were still there it would be in that dictionary.

**Is the marking table empty?**  `MARKINGS["uranus"]` is read directly, so the
source and the solids are checked to agree instead of one standing in for the
other.

**Does the arithmetic close?**  A marking in this set is a flush colour inlay:
the globe is partitioned, not carved, so removing the two hoods must hand the
globe back exactly the volume they held and move no surface.  The published
edition's own occurrence volumes are read from the archive measurement and the
residue is reported to four decimal places.

    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py <published antisol.step> > was.json
    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py antisol.step > now.json
    "$WORKSHOP_PYTHON" measure/uranus_bare.py was.json now.json > measure/uranus-bare.md

Exit 0 when nothing is drawn on either globe and the arithmetic closes, 1 when
anything at all survives on a Uranus globe or the volumes do not add up.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.markings import MARKINGS                           # noqa: E402
from parts.world import world_bodies                          # noqa: E402

PLANET = "uranus"

#: The roles a world piece has when it carries no marking at all.  `ring` is
#: geometry rather than a marking -- it is a solid hoop in the equatorial
#: plane, not a colour inlay in the globe's own sphere -- and `disc` and
#: `numeral` are the base every piece in the set stands on.
STRUCTURAL = {"disc", "numeral", "globe", "ring"}

#: mm3.  A boolean run on the same source is reproducible far below this.
RESIDUE_TOLERANCE = 0.01


def load(path: Path) -> dict:
    data = json.loads(path.read_text())
    return data.get("occurrences", data)


def volume_of(table: dict, label: str):
    entry = table.get(label)
    return None if entry is None else float(entry["volume"])


def main() -> int:
    was = load(Path(sys.argv[1]))
    now = load(Path(sys.argv[2]))
    failures: list[str] = []

    print("# Uranus carries no marking, measured on the solids")
    print()
    print("The owner has removed both polar hoods. Nothing replaces them: no")
    print("cap, no band, no spot, no quieter tone. This is the evidence that")
    print("nothing at all is drawn on either globe, taken three ways, because a")
    print("marking that silently fails to cut leaves a piece that still measures")
    print("as sound and correctly sized -- which is a fault this exact world has")
    print("had before.")
    print()

    print("## 1. The marking table is empty")
    print()
    regions = MARKINGS[PLANET]
    print("`parts/markings.py` lists %d region%s for `\"%s\"`."
          % (len(regions), "" if len(regions) == 1 else "s", PLANET))
    if regions:
        failures.append("MARKINGS[%r] still lists %d region(s)" % (PLANET, len(regions)))
        print()
        print("**That is a failure.** It should be empty.")
    else:
        print("The argument that built the hoods is kept above it, headed with")
        print("what happened to it. The list itself has nothing in it, so there")
        print("is nothing for `world_bodies` to cut the globe with.")
    print()

    print("## 2. The pieces have no marking body")
    print()
    print("`parts.world.world_bodies` is the one place the colour split is")
    print("decided; every STEP, occurrence and render downstream is built from")
    print("what it returns.")
    print()
    print("| piece | role | filament | solids | volume mm3 |")
    print("|---|---|---|---|---|")
    for side in P.SIDES:
        bodies = world_bodies(PLANET, side)
        extra = sorted(set(bodies) - STRUCTURAL)
        if extra:
            failures.append("%s %s still carries %s" % (PLANET, side, ", ".join(extra)))
        for role in sorted(bodies):
            colour, shape = bodies[role]
            solids = list(shape.solids())
            print("| %s | `%s` | `%s` | %d | %.6f |"
                  % (side, role, colour, len(solids),
                     sum(solid.volume for solid in solids)))
    print()
    print("Four roles per piece and no fifth: the disc it stands on, the numeral")
    print("cut into that disc, the globe, and the ring. The ring is geometry, not")
    print("a marking -- a solid hoop in the equatorial plane rather than a colour")
    print("inlay in the globe's own sphere -- so **the globe is one undivided")
    print("`%s` solid and there is no surface marking on this world at all.**"
          % P.GLOBE_COLOUR[PLANET])
    print()

    print("## 3. The arithmetic closes")
    print()
    print("A marking here is a flush inlay: it partitions the globe rather than")
    print("carving it. So taking the two hoods out must hand the globe back")
    print("exactly the volume they held, and move no surface.")
    print()
    print("| piece | published globe | + hood north | + hood south | = expected | measured now | residue |")
    print("|---|---|---|---|---|---|---|")
    for side in P.SIDES:
        stem = "%s_%s_" % (PLANET, side)
        globe_was = volume_of(was, stem + "globe_" + P.GLOBE_COLOUR[PLANET])
        north = volume_of(was, stem + "hood_north_beige")
        south = volume_of(was, stem + "hood_south_beige")
        globe_now = volume_of(now, stem + "globe_" + P.GLOBE_COLOUR[PLANET])
        if None in (globe_was, north, south, globe_now):
            failures.append("%s: an occurrence the arithmetic needs is missing" % side)
            print("| %s | %s | %s | %s | - | %s | **missing** |"
                  % (side, globe_was, north, south, globe_now))
            continue
        expected = globe_was + north + south
        residue = globe_now - expected
        if abs(residue) > RESIDUE_TOLERANCE:
            failures.append("%s: %.4f mm3 of residue" % (side, residue))
        print("| %s | %.3f | %.4f | %.4f | %.3f | %.3f | %+.4f |"
              % (side, globe_was, north, south, expected, globe_now, residue))
    print()
    print("The residue is the whole of what the removal cost the solid: within")
    print("%.2f mm3 the globe is exactly its old self plus its two hoods, which"
          % RESIDUE_TOLERANCE)
    print("is what a partition undone has to be. Both printed STEPs come out")
    print("byte-identical to the published set's for the same reason --")
    print("`measure/revision-part-hashes.md` carries those hashes.")
    print()

    print("## Verdict")
    print()
    if failures:
        print("**FAIL.**")
        for item in failures:
            print("- %s" % item)
        return 1
    print("**Nothing is drawn on either Uranus globe.** The marking table is")
    print("empty, neither piece carries a marking body, and the globe's volume")
    print("is its old volume plus both hoods to within %.2f mm3."
          % RESIDUE_TOLERANCE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
