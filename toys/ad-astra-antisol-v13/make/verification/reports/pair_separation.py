"""How far apart do a world's two pieces actually read?

The owner's complaint was that looking from one side, the Mercury and the Venus
of both armies are on the same side -- that each of those pairs is one piece
photographed twice rather than two pieces.  This puts a number on that, for all
eight worlds, so the answer is a measurement rather than an impression, and so
that Jupiter -- which has the same condition and is deliberately NOT in scope --
can be reported as a number the owner can choose from.

Two separate questions, because a pair is separated by two different things.

THE LEAN is the set's own ownership cue: `planet_frame` turns the Sol globe by
+tilt and the Anti-Sol globe by -tilt, so the two poles stand apart by an angle
that is pure arithmetic on the obliquity.  That is table one, and it is where
Mercury, Venus and Jupiter fail: 0.06, 5.28 and 6.26 degrees.

THE SURFACE is what this correction changes, and it is measured on the BUILT
COLOUR BODIES rather than on the marking table.  Every marking solid's centre
of mass gives a direction out of the globe's centre; that direction is
projected into the camera's own image plane at the two photographed frames, and
the two pieces' sets of markings are compared as sets.  Set-wise rather than
body by body on purpose: `X.parts` numbers a colour's separate solids in
whatever order the kernel hands them over, so `plains1` on one piece is not
necessarily the same patch as `plains1` on the other, and a body-by-body
comparison would be measuring the numbering.

    "$WORKSHOP_PYTHON" measure/pair_separation.py [--before] > measure/pair-separation.md

`--before` empties `markings.MAP_MIRRORED_WORLDS` first and measures the set as
it was before this correction, so the two runs can be laid side by side.  It
changes nothing on disk and builds nothing the product ships.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bool3d as X                                             # noqa: E402
import params as P                                             # noqa: E402
from parts import markings as M                                # noqa: E402
from parts.world import world_bodies                           # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                  # noqa: E402

FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))

#: Roles that are the piece rather than the planet's surface.  A disc, a
#: numeral and a ring are ownership cues carried by other machinery; the globe
#: is the ball the markings are cut out of.
NOT_SURFACE = ("disc", "numeral", "globe", "ring")

#: A marking solid this small is a sliver the split left behind rather than
#: something a reader sees.  Venus's buried Ishtar fragment is 3.04 mm3 and is
#: inside the seat collar in any case.
MIN_BODY_MM3 = 0.5


def is_surface(role: str) -> bool:
    return not any(role.startswith(name) for name in NOT_SURFACE)


def view_basis(azimuth: float, elevation: float):
    """(view axis, screen right, screen up) for `render_review`'s camera."""
    az, el = math.radians(azimuth), math.radians(elevation)
    axis = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
            math.sin(el))
    right = (-math.sin(az), math.cos(az), 0.0)
    up = (axis[1] * right[2] - axis[2] * right[1],
          axis[2] * right[0] - axis[0] * right[2],
          axis[0] * right[1] - axis[1] * right[0])
    return axis, right, up


def dot(one, other):
    return sum(a * b for a, b in zip(one, other))


def marking_solids(planet: str, side: str):
    """(filament, unit direction, volume) for every marking solid on a piece."""
    centre_z = P.globe_centre_z(planet)
    out = []
    for role, (colour, shape) in world_bodies(planet, side).items():
        if not is_surface(role):
            continue
        for solid in X.parts(shape):
            if solid.volume < MIN_BODY_MM3:
                continue
            point = solid.center()
            vector = (point.X, point.Y, point.Z - centre_z)
            length = math.sqrt(dot(vector, vector))
            if length < 1e-9:
                continue
            out.append((colour,
                        tuple(value / length for value in vector),
                        solid.volume))
    return out


def project(items, view, radius: float, flip: bool = False):
    """Visible markings as (filament, u, v, volume) in millimetres on screen."""
    axis, right, up = view_basis(*view)
    seen = []
    for colour, unit, volume in items:
        if dot(unit, axis) <= 0.0:
            continue
        u = dot(unit, right) * radius
        v = dot(unit, up) * radius
        seen.append((colour, -u if flip else u, v, volume))
    return seen


def set_distance(left, right_set) -> float:
    """Volume-weighted mean distance from each left marking to its nearest
    same-filament neighbour on the right, symmetrised over the two directions.

    Nearest-neighbour rather than paired, because the two pieces' solids are
    not numbered comparably.  Same filament only: a beige highland is not
    answered by a cocoa lowland sitting where it used to be.
    """

    def one_way(source, target):
        weighted, weight = 0.0, 0.0
        for colour, u, v, volume in source:
            peers = [item for item in target if item[0] == colour]
            if not peers:
                continue
            nearest = min(math.hypot(u - other[1], v - other[2])
                          for other in peers)
            weighted += nearest * volume
            weight += volume
        return None if weight == 0.0 else weighted / weight

    forward = one_way(left, right_set)
    back = one_way(right_set, left)
    values = [item for item in (forward, back) if item is not None]
    return sum(values) / len(values) if values else None


def lean_separation(planet: str) -> float:
    """The angle between the two pieces' north-pole directions, in degrees."""
    tilt = P.PLANETS[planet]["tilt"]
    angle = 2.0 * tilt
    return angle if angle <= 180.0 else 360.0 - angle


def main() -> int:
    before = "--before" in sys.argv[1:]
    if before:
        M.MAP_MIRRORED_WORLDS = ()
        M.markings_for.cache_clear()

    order = sorted(P.PLANETS, key=lambda name: P.PLANETS[name]["rank"])
    solids = {(planet, side): marking_solids(planet, side)
              for planet in order for side in P.SIDES}

    print("# How far apart the two pieces of each pair read%s"
          % (" -- BEFORE this correction" if before else ""))
    print()
    if before:
        print("**This run measures the set as it was.**")
        print("`markings.MAP_MIRRORED_WORLDS` was emptied before building, so")
        print("every Anti-Sol piece carries its map at the same longitudes as")
        print("its Sol twin and the only thing separating a pair is the lean.")
        print("It is here to be laid beside the corrected run.")
        print()

    print("## One: the lean")
    print()
    print("`features.planet_frame` turns the Sol globe about +Y by the planet's")
    print("true obliquity and the Anti-Sol globe by minus it, so the two poles")
    print("stand apart by twice the tilt -- or by 360 less twice the tilt when")
    print("that exceeds a half turn, because a lean of +177.36 and one of")
    print("-177.36 are the same turn measured each way round. This is pure")
    print("arithmetic on `params.PLANETS`; nothing here is built.")
    print()
    print("| world | obliquity | the two poles stand apart by | the lean gives the pair |")
    print("|---|---:|---:|---|")
    for planet in order:
        gap = lean_separation(planet)
        if gap < 10.0:
            verdict = "**nothing**"
        elif gap < 20.0:
            verdict = "very little"
        else:
            verdict = "a plain difference"
        print("| %s | %.2f | %.2f degrees | %s |"
              % (planet, P.PLANETS[planet]["tilt"], gap, verdict))
    print()
    print("Three worlds are degenerate and five are not. Mercury at 0.06")
    print("degrees and Venus at 5.28 are the two this correction is for.")
    print("Jupiter at 6.26 has the same condition and is NOT in scope: the")
    print("owner named Mercury and Venus and did not name it. Mars at 50.38,")
    print("Earth at 46.88, Saturn at 53.46, Neptune at 56.64 and Uranus at")
    print("164.46 are nowhere near it, which is the negative half of the same")
    print("check and is why the recommendation below is scoped to Jupiter alone.")
    print()

    print("## Two: the surface")
    print()
    print("Measured on the built colour bodies. Every marking solid's centre of")
    print("mass gives a direction out of the globe's centre; that direction is")
    print("projected into the camera's image plane at the two photographed")
    print("frames. Distances are millimetres on that globe's own surface.")
    print()
    print("- **separation** -- how far a marking is from the nearest marking of")
    print("  the same filament on the other piece. Near zero means the pair is")
    print("  one object photographed twice.")
    print("- **mirror residual** -- the same distance measured against a")
    print("  left-to-right flip of the other piece's picture. Near zero means")
    print("  the pair reads as a mirror pair rather than as two unrelated faces.")
    print()
    print("Both are volume-weighted, so a large province counts for more than a")
    print("sliver, and both are symmetrised over the two directions.")
    print()
    print("| world | globe Ømm | frame | visible markings, Sol / Anti | separation | mirror residual |")
    print("|---|---:|---|---|---:|---:|")
    surface = {}
    for planet in order:
        radius = P.globe_radius(planet)
        for label, view in FRAMES:
            sol = project(solids[(planet, "sol")], view, radius)
            anti = project(solids[(planet, "anti")], view, radius)
            flipped = project(solids[(planet, "sol")], view, radius, flip=True)
            gap = set_distance(sol, anti)
            mirror = set_distance(flipped, anti)
            surface[(planet, label)] = gap
            print("| %s | %.2f | %s | %d / %d | %s | %s |"
                  % (planet, P.globe_diameter(planet), label,
                     len(sol), len(anti),
                     "no marking" if gap is None else "%.3f" % gap,
                     "no marking" if mirror is None else "%.3f" % mirror))
    print()
    print("Uranus has no marking of any kind since the run before this one --")
    print("one undivided cyan sphere -- so there is nothing on its surface to")
    print("compare and the row says so rather than reporting a zero. Its pair is")
    print("separated by the lean, at 164.46 degrees, and by the plane its ring")
    print("stands in, which follows that lean.")
    print()

    print("## Read in rank order, on the frame that separates them least")
    print()
    print("| world | obliquity | lean | least surface separation | reads as |")
    print("|---|---:|---:|---:|---|")
    for planet in order:
        values = [surface[(planet, label)] for label, _v in FRAMES
                  if surface[(planet, label)] is not None]
        radius = P.globe_radius(planet)
        if not values:
            print("| %s | %.2f | %.2f | no marking | the lean alone, at %.2f degrees |"
                  % (planet, P.PLANETS[planet]["tilt"], lean_separation(planet),
                     lean_separation(planet)))
            continue
        least = min(values)
        share = least / radius
        if share < 0.10:
            verdict = "**one object photographed twice**"
        elif share < 0.25:
            verdict = "barely two objects"
        else:
            verdict = "two different objects"
        print("| %s | %.2f | %.2f | %.3f mm (%.0f%% of the globe radius) | %s |"
              % (planet, P.PLANETS[planet]["tilt"], lean_separation(planet),
                 least, 100.0 * share, verdict))
    print()
    print("The share of the globe radius is the honest way to compare across the")
    print("ladder: Mercury's globe is Ø13.78 and Jupiter's Ø26.97, so a")
    print("millimetre means about twice as much on the smaller ball.")
    print()

    print("## Measured by")
    print()
    print("`measure/pair_separation.py`, on the solids `parts/world.py` builds")
    print("and the cameras in `snap_frames.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
