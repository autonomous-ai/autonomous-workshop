"""Saturn's ring is a solid, so it is checked as a solid.

`measure/occurrence-geometry.md` proves that nothing OUTSIDE the two Saturn
pieces gained, lost or moved a solid.  That is the wrong question for the ring,
because the ring is inside those two pieces: a change to it would be permitted
by that report rather than flagged by it.

The correction brief is explicit that the ring system is not part of this
revision and must not move, and that because the ring is a solid rather than a
colour inlay it has to be confirmed on solid count, volume and bounding box
rather than on colour alone.  This is that confirmation, made against the same
two occurrence dumps `measure/occurrence_geometry.py` writes, and it names the
occurrences rather than inferring them from a prefix.

It also re-reads every value in the ring block of `params.py` and prints it
beside the published number, so that "unchanged" covers the parameters as well
as the built solid.

    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py <published assembly.step> > was.json
    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py antisol.step > now.json
    "$WORKSHOP_PYTHON" measure/saturn_ring_unchanged.py was.json now.json \\
        > measure/saturn-ring-unchanged.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402

#: The occurrences this revision is required to leave exactly where they were.
#: The ring itself on both armies, and -- because a correction that moved the
#: globe's own boundary or the disc under it would also be outside the brief --
#: the disc and the numeral strokes beside it.
HELD = {
    "the ring": ("saturn_sol_ring_white", "saturn_anti_ring_white"),
    "the disc": ("saturn_sol_disc_white", "saturn_anti_disc_black"),
    "the numeral": ("saturn_sol_numeral1_black", "saturn_sol_numeral2_black",
                    "saturn_sol_numeral3_black", "saturn_sol_numeral4_black",
                    "saturn_anti_numeral1_white", "saturn_anti_numeral2_white",
                    "saturn_anti_numeral3_white", "saturn_anti_numeral4_white"),
}

#: The published values of the ring block, quoted from the brief rather than
#: read from this build, so the comparison has an independent left-hand side.
PUBLISHED_RING = (
    ("RING_INNER_D", 26.00),
    ("RING_OUTER_D", 30.00),
    ("RING_THICKNESS", 1.40),
    ("RING_GLOBE_BITE", 1.00),
    ("RING_WEB_SECTORS", 96),
    ("RING_WEB_INNER_R", 5.00),
    ("RING_WEB_OVERLAP", 0.45),
    ("RING_WEB_DROP", 0.30),
    ("RING_WEB_SLOPE", 1.08),
)

VOLUME_TOLERANCE = 1e-4
BOX_TOLERANCE = 1e-6


def main() -> int:
    was = json.loads(Path(sys.argv[1]).read_text())["occurrences"]
    now = json.loads(Path(sys.argv[2]).read_text())["occurrences"]

    print("# Saturn's ring did not move")
    print()
    print("The ring is a solid rather than a colour inlay, so `occurrence-")
    print("geometry.md`'s verdict -- *nothing outside the two Saturn pieces")
    print("changed* -- does not cover it: the ring is inside those two pieces and")
    print("a change to it would pass that test rather than fail it. This asks the")
    print("question of the ring by name.")
    print()

    print("## The ring block of `params.py`")
    print()
    print("| value | published | this build | |")
    print("|---|---:|---:|---|")
    drifted = []
    for name, published in PUBLISHED_RING:
        current = getattr(P, name)
        same = abs(current - published) < 1e-9
        if not same:
            drifted.append(name)
        print("| `%s` | %s | %s | %s |"
              % (name,
                 ("%d" % published) if isinstance(published, int) else "%.2f" % published,
                 ("%d" % current) if isinstance(current, int) else "%.2f" % current,
                 "unchanged" if same else "**MOVED**"))
    print()
    if drifted:
        print("**%s moved.**" % ", ".join("`%s`" % name for name in drifted))
    else:
        print("**Every value in the ring block is the one the published set had.**")
    print()

    print("## The built solids, occurrence by occurrence")
    print()
    print("Solid count, exact volume and bounding box, from the same two dumps")
    print("`measure/occurrence_geometry.py` writes, at %g mm3 and %g mm."
          % (VOLUME_TOLERANCE, BOX_TOLERANCE))
    print()
    print("| occurrence | solids | published mm3 | this run mm3 | box drift mm | |")
    print("|---|---:|---:|---:|---:|---|")
    failures = []
    for label, names in HELD.items():
        for name in names:
            left, right = was.get(name), now.get(name)
            if left is None or right is None:
                failures.append("%s is missing from one of the two runs" % name)
                print("| `%s` | -- | -- | -- | -- | **MISSING** |" % name)
                continue
            drift = max(
                abs(a - b)
                for key in ("min", "max")
                for a, b in zip(left[key], right[key])
            )
            same = (left["solids"] == right["solids"]
                    and abs(left["volume"] - right["volume"]) <= VOLUME_TOLERANCE
                    and drift <= BOX_TOLERANCE)
            if not same:
                failures.append(name)
            print("| `%s` | %d | %.6f | %.6f | %.2e | %s |"
                  % (name, right["solids"], left["volume"], right["volume"],
                     drift, "identical" if same else "**MOVED**"))
    print()
    if failures:
        print("**Moved: %s**" % ", ".join("`%s`" % name for name in failures))
        return 1
    print("**Every held occurrence is identical on all three measures.** The ring")
    print("is one solid on each army, at the same volume, in the same box as the")
    print("published set to %g mm3 and %g mm -- and so are the disc and the four"
          % (VOLUME_TOLERANCE, BOX_TOLERANCE))
    print("numeral strokes beside it. This revision changed where")
    print("the colour boundary falls on the globe and nothing else on the piece.")
    print()
    print("Measured by `measure/saturn_ring_unchanged.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
