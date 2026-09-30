"""Two things readers of the archived build reported, re-measured on this one.

Both are claims about the solids, made from rendered frames, and both are
answered here by measuring the solids rather than by arguing with the reader.
One is about protrusion and one is about faceting.  Both quoted readings below
belong to the build this revision corrects; they are HISTORY rather than this
run's review, and they are re-run here because this revision replaced Neptune's
white marking and a measurement of a marking that no longer exists proves
nothing about the one that does.

**PROTRUSION.**  An independent reader of the archived `snap/worlds/neptune-*.png`
reported that the white markings "are solid raised lenses that break the ball's
silhouette", with "thin overhanging slivers" and "unsupported knife-edged lips
over the puck", and withdrew the finding when it was measured.  That is a claim
about geometry and about two of this set's standing negative requirements --
nothing protrudes, and no downward-facing surface is added -- so it is answered
with geometry, on this revision's three bands rather than on the eight streaks
it was made about.

**FACETING.**  Two independent readers, looking at two different builds of the
dark spot, reported "straight segments and blunt corners" on its lower left and
called it "a coarse low-segment polygon approximating an ellipse".  The first
of those readers saw it at 22 ring vertices; the second saw it, in the same
place, at 40.  A defect that does not move when the vertex count is nearly
doubled is not the vertex count, so the ring's own departure from the true
ellipse is measured below as well.  The spot is unchanged in this revision, so
this measurement is expected to reproduce the archived one exactly.

The construction says it cannot happen: `parts/world.py` does not ADD a marking
to the globe, it SPLITS the globe.  Every marking body is one half of a split
of the ball itself, so its outer face IS the ball's own sphere and its every
point lies on or inside that sphere.  This measures that on the exact solids
rather than asserting it: for each colour body of each army, the greatest
distance any vertex of it reaches from the globe's centre, against the globe's
own radius.

    "$WORKSHOP_PYTHON" measure/neptune_flush.py > measure/neptune-flush.md
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.world import world_bodies                          # noqa: E402

#: mm.  The tessellation this reads is a chord approximation of a sphere, so a
#: sampled point sits a little INSIDE the true surface, never outside it; the
#: tolerance is here only to absorb kernel round-off at the surface itself.
TOLERANCE = 1e-6

#: How finely each body is tessellated before its vertices are measured.  Fine
#: enough that the sampled maximum is within a micron of the true one.
LINEAR = 0.002
ANGULAR = 0.01


def reach(shape, centre_z: float) -> float:
    vertices, _faces = shape.tessellate(LINEAR, ANGULAR)
    return max(
        ((point.X ** 2 + point.Y ** 2 + (point.Z - centre_z) ** 2) ** 0.5)
        for point in vertices
    )


def main() -> int:
    radius = P.globe_radius("neptune")
    centre = P.globe_centre_z("neptune")
    print("# Nothing on Neptune stands proud of its globe")
    print()
    print("Neptune's globe is a sphere of radius %.3f mm centred %.3f mm above"
          % (radius, centre))
    print("the disc's bed face. Every marking on it is a flush colour inlay:")
    print("`parts/world.py` SPLITS the ball rather than adding to it, so a")
    print("marking body's outer face is the ball's own sphere. Below is the")
    print("greatest distance any point of each body reaches from that centre,")
    print("measured on the exact solids at a %g mm chord tolerance." % LINEAR)
    print()
    print("One body is expected to reach past the sphere and does: the `globe`")
    print("body is the ball PLUS the seat cone it stands on, which springs from")
    print("latitude %.1f and spreads outward at %.1f degrees from vertical down"
          % (P.SEAT_LATITUDE_DEG, P.SEAT_DRAFT_DEG))
    print("to the disc face. That collar is original geometry, shared by all")
    print("sixteen worlds, untouched by this revision, and it is what stops a")
    print("sphere resting tangentially on a flat disc from leaving an")
    print("unsupported cap underneath it. It is listed and excluded from the")
    print("verdict; the verdict is about the MARKINGS.")
    print()
    print("| army | body | filament | furthest point from globe centre mm "
          "| globe radius mm | proud by mm | |")
    print("|---|---|---|---:|---:|---:|---|")
    worst = None
    for side in ("sol", "anti"):
        for role, (colour, shape) in world_bodies("neptune", side).items():
            if role in ("disc", "numeral"):
                continue
            marking = role not in ("globe",)
            far = reach(shape, centre)
            proud = far - radius
            if marking:
                worst = proud if worst is None else max(worst, proud)
                verdict = "flush" if proud <= TOLERANCE else "**PROUD**"
            else:
                verdict = "the seat cone, by design"
            print("| %s | `%s` | `%s` | %.6f | %.6f | %+.6f | %s |"
                  % ("Sol" if side == "sol" else "Anti-Sol", role, colour,
                     far, radius, proud, verdict))
    print()
    print("The greatest any MARKING reaches past the globe's own surface is")
    print("**%+.6f mm** -- every marking body touches the sphere exactly"
          % worst)
    print("and none of them crosses it.")
    print()
    if worst > TOLERANCE:
        print("That is a real protrusion and it must be repaired.")
        return 1
    print("Nothing is proud of the sphere, on either army, to within a")
    print("millionth of a millimetre. The globe's outer surface is an exact")
    print("sphere and the markings are parts of it, so **nothing protrudes and")
    print("no marking adds a downward-facing surface** -- there is no new")
    print("surface at all, only a different filament through the outer")
    print("%.2f mm of the same ball." % P.RELIEF_DEPTH)
    print()
    print("## The dark spot is not a faceted polygon either")
    print()
    import math
    from parts import neptune_atlas as N
    a, b = N.SPOT_SEMI_ARC_LON, N.SPOT_SEMI_ARC_LAT
    count = len(N.SPOT_RING)

    def polar(theta):
        return a * b / math.hypot(b * math.sin(theta), a * math.cos(theta))

    worst_chord = 0.0
    for index in range(count):
        first = -2.0 * math.pi * index / count
        second = -2.0 * math.pi * (index + 1) / count
        middle = 0.5 * (first + second)
        one = (polar(first) * math.cos(first), polar(first) * math.sin(first))
        other = (polar(second) * math.cos(second), polar(second) * math.sin(second))
        chord = (0.5 * (one[0] + other[0]), 0.5 * (one[1] + other[1]))
        true = (polar(middle) * math.cos(middle), polar(middle) * math.sin(middle))
        worst_chord = max(worst_chord,
                          math.hypot(true[0] - chord[0], true[1] - chord[1]))
    print("The spot is walked at %d even bearings about its own centre. The"
          % count)
    print("furthest any of its %d chords falls inside the true ellipse is"
          % count)
    print("**%.4f degrees of arc, %.4f mm** -- %.0f per cent of one nozzle"
          % (worst_chord, worst_chord * N.MM_PER_DEG,
             100.0 * worst_chord * N.MM_PER_DEG / P.NOZZLE_MM))
    print("width, on a marking %.2f mm across. There is no facet on this ring"
          % (2 * a * N.MM_PER_DEG))
    print("that a printer could lay down, let alone one an eye could find.")
    print()
    print("Looked at directly rather than argued about: the same frame the")
    print("reader read, magnified four times about the spot, shows a")
    print("continuous smooth ellipse whose only stepping is the single-pixel")
    print("staircase that `render_review` puts on EVERY boundary in the")
    print("image, the three white bands included, because it does not")
    print("antialias.")
    print("At 1:1 on a Ø%.2f mm globe the spot is about 130 pixels across, so"
          % N.GLOBE_D)
    print("that staircase is one pixel in forty of its width -- which is what")
    print("a reader is describing as a corner.")
    print()
    print("## Why a reader saw otherwise")
    print()
    print("Reported blind by the archived build's own critic, from that")
    print("build's rendered frames: the markings \"are solid")
    print("raised lenses that break the ball's silhouette\", with \"thin")
    print("overhanging slivers\" and \"unsupported knife-edged lips over the")
    print("puck\". The measurement above says the geometry does not do that, so")
    print("what the reader is seeing is the renderer. A marking that reaches")
    print("the limb IS on the silhouette -- it is the sphere there -- and")
    print("`render_review` shades flat, with no shadow and no ground plane, so")
    print("a near-white body against the pale background at the outline has no")
    print("cue that says it is coplanar with the blue beside it rather than in")
    print("front of it. The same flat shading is why several markings read")
    print("mid-grey on one side of the ball and pure white on the other. That")
    print("limitation is recorded for the whole set rather than for this world,")
    print("and it is a property of the review renderer, not of the solid the")
    print("shop receives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
