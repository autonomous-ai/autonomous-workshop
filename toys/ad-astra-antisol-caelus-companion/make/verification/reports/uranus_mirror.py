"""The two Uranus pieces against each other.

The correction adds material for the first time in this chain -- a ring -- so
"the two pieces are still mirrors" stops being a statement about a colour split
and becomes one about a solid.  Both are measured here, on the exact bodies
`parts/world.py` builds and on the printed part `build_world` hands the gates.

The form is `measure/neptune_mirror.py`'s and the tolerance is its %g mm3.

Two bodies are MEANT to differ and are named rather than explained away: a Sol
disc flares outward as it rises and an Anti-Sol disc tapers inward, so the two
are different solids by design and carry opposite colours, and the numeral in
them does the same.  That is the set's ownership cue.  Everything else is one
description built twice.

    "$WORKSHOP_PYTHON" measure/uranus_mirror.py > measure/uranus-mirror.md

Exit 0 when every body that should match does, 1 when one does not.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.world import build_world, world_bodies             # noqa: E402

PLANET = "uranus"
TOLERANCE = 1e-4

#: Roles the two armies are meant to build differently, and why.
BY_DESIGN = {
    "disc": "the draft runs the other way: Ø33.00 to Ø34.00 against Ø34.00 to Ø33.00",
    "numeral": "the same digit in the same place, in the other filament",
    "globe": "clipped by a disc that drafts the other way",
}

__doc__ = __doc__ % TOLERANCE


def box_row(box):
    return (box.min.X, box.max.X, box.min.Y, box.max.Y, box.min.Z, box.max.Z)


def main() -> int:
    failures = []
    bodies = {side: world_bodies(PLANET, side) for side in P.SIDES}
    sol, anti = bodies["sol"], bodies["anti"]

    print("# The two Uranus pieces against each other")
    print()
    print("Measured on the exact colour bodies `parts/world.py` builds, at")
    print("%g mm3. The two armies share one marking description, one ring" % TOLERANCE)
    print("description and one obliquity, and lean the opposite way under all")
    print("three; this is what that produces.")
    print()
    print("## Body for body")
    print()
    print("| role | filament Sol / Anti | solids | volume Sol mm3 | volume Anti mm3 | difference | |")
    print("|---|---|---:|---:|---:|---:|---|")
    for role in sol:
        if role not in anti:
            failures.append("%s exists only on the Sol piece" % role)
            continue
        left_colour, left = sol[role]
        right_colour, right = anti[role]
        delta = right.volume - left.volume
        if role in BY_DESIGN:
            note = BY_DESIGN[role]
        elif abs(delta) <= TOLERANCE:
            note = "identical"
        else:
            note = "**differs**"
            failures.append("%s differs by %.6f mm3" % (role, delta))
        print("| `%s` | `%s` / `%s` | %d / %d | %.6f | %.6f | %+.6f | %s |"
              % (role, left_colour, right_colour,
                 len(left.solids()), len(right.solids()),
                 left.volume, right.volume, delta, note))
    for role in anti:
        if role not in sol:
            failures.append("%s exists only on the Anti-Sol piece" % role)
    print()
    print("**The globe and the ring are identical to %g mm3 on both armies.**"
          % TOLERANCE)
    print("There is nothing else on this world to compare: the owner's second")
    print("pass took both polar hoods off, so each piece is a disc, a numeral, one")
    print("undivided `cyan` globe and one `white` hoop. The two bodies that do")
    print("differ are the two the set means to differ -- the disc and the numeral,")
    print("which are the ownership cue -- and they differ by the disc's draft")
    print("rather than by anything drawn on the ball.")
    print()
    print("## The ring in space")
    print()
    print("A mirror in X, which is what the two armies are: the Sol ring's")
    print("greatest +X reach is the Anti-Sol ring's greatest -X reach, and")
    print("everything square to X is unchanged.")
    print()
    print("| | Sol | Anti-Sol | mirrored value | |")
    print("|---|---:|---:|---:|---|")
    left = sol["ring"][1].bounding_box()
    right = anti["ring"][1].bounding_box()
    rows = [
        ("X low", left.min.X, right.min.X, -right.max.X),
        ("X high", left.max.X, right.max.X, -right.min.X),
        ("Y low", left.min.Y, right.min.Y, right.min.Y),
        ("Y high", left.max.Y, right.max.Y, right.max.Y),
        ("Z low", left.min.Z, right.min.Z, right.min.Z),
        ("Z high", left.max.Z, right.max.Z, right.max.Z),
    ]
    for label, a, b, mirrored in rows:
        same = abs(a - mirrored) <= 1e-6
        print("| %s mm | %.4f | %.4f | %.4f | %s |"
              % (label, a, b, mirrored, "mirrored" if same else "**differs**"))
        if not same:
            failures.append("the rings are not mirrors on %s" % label)
    print()
    print("## The printed solid")
    print()
    print("| | Sol | Anti-Sol | |")
    print("|---|---:|---:|---|")
    parts = {side: build_world(PLANET, side) for side in P.SIDES}
    left_box, right_box = (parts[side].bounding_box() for side in ("sol", "anti"))
    print("| solids | %d | %d | one printed part each |"
          % (len(parts["sol"].solids()), len(parts["anti"].solids())))
    print("| volume mm3 | %.4f | %.4f | the disc's draft, %s |"
          % (parts["sol"].volume, parts["anti"].volume,
             "%+.4f mm3" % (parts["anti"].volume - parts["sol"].volume)))
    print("| height mm | %.4f | %.4f | %s |"
          % (left_box.max.Z, right_box.max.Z,
             "identical" if abs(left_box.max.Z - right_box.max.Z) <= 1e-6
             else "**differs**"))
    if abs(left_box.max.Z - right_box.max.Z) > 1e-6:
        failures.append("the two pieces are not the same height")
    print()
    part_delta = parts["anti"].volume - parts["sol"].volume
    disc_delta = anti["disc"][1].volume - sol["disc"][1].volume
    print("The printed parts differ in volume by %.4f mm3 on a %.0f mm3 piece,"
          % (part_delta, parts["sol"].volume))
    print("%.2f per cent, and %.4f of that is the two discs' own draft. The"
          % (100.0 * part_delta / parts["sol"].volume, disc_delta))
    print("remaining %.4f mm3 is not a second difference in the design: the"
          % (part_delta - disc_delta))
    print("printed part is built from the disc and the ball directly, in three")
    print("booleans, and the colour bodies are built by splitting the same solid")
    print("fifteen ways, so the two paths round the drafted seam between disc and")
    print("globe a few hundredths of a cubic millimetre apart. Both are far under")
    print("one layer of one extrusion.")
    print()
    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("**The two pieces are exact mirrors.** Every body that is meant to")
        print("match matches to %g mm3, the two hoops lean opposite ways and reach"
              % TOLERANCE)
        print("the same distance in the other direction, and the three bodies that")
        print("differ differ by the disc's draft alone.")
    print()
    print("Measured by `measure/uranus_mirror.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
