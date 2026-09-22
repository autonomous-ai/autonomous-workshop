"""Which pole faces the camera, on which army, at which frame.

Uranus lies on its side.  Its obliquity is 97.77 degrees, so the pole is 7.77
degrees PAST horizontal, and the two armies lean opposite ways: whatever the
Sol piece turns toward the lens, the Anti-Sol piece turns away.  A marking that
lives at one pole is therefore a marking one whole army may never show, and the
Wish asks for that to be measured at both photographed frames rather than
assumed.

This is `measure/venus_facing.py`'s and `measure/neptune_facing.py`'s method:
the exact colour bodies `parts/world.py` builds are sampled on their own
surfaces, and every sample is dotted against the view axis of each canonical
camera.  A sample with a positive dot is on the hemisphere the camera can see.
Nothing here is read off a render.

Three questions are answered for each army at each frame.

**Is the hood on the visible face at all?**  The fraction of the hood's own
surface samples that face the camera.

**Where on the face does it sit?**  The angular distance of the pole from the
view axis, and the same expressed as a fraction of the globe's silhouette
radius: 0.00 is the dead centre of the visible disc and 1.00 is the limb.

**Does the ring fight it?**  Where each body lands in projection, as a
distance from the piece's own axis in the image plane divided by the globe's
radius: under 1.00 is inside the globe's silhouette, over 1.00 is outside it.
That is what says whether the ring projects as a halo round the rim while the
hood occupies face.

    "$WORKSHOP_PYTHON" measure/uranus_facing.py > measure/uranus-facing.md

Exit 0 when every army shows a hood at every frame, 1 when one does not.
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
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402

PLANET = "uranus"
FRAMES = {"hero (-55, 22)": HERO_VIEW, "sheet (-45, 35.264)": SHEET_VIEW}

#: How much of a hood has to face the camera before a reader would call it
#: visible.  A hood grazing the limb shows a sliver that reads as a rim
#: highlight rather than as a marking; this project's own Saturn cap report
#: used the same shape of test.
VISIBLE_FRACTION = 0.10

#: How finely a body is sampled.  The question is a direction, not a length, so
#: a coarse tessellation is plenty and a fine one only costs time.
TOLERANCE = 0.12


def view_axis(azimuth_deg: float, elevation_deg: float):
    """The unit vector from the object toward the camera.

    `render_review` puts the camera at that azimuth and elevation, east to the
    right, so this is the direction a surface has to face to be seen.
    """
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    return (
        math.cos(elevation) * math.cos(azimuth),
        math.cos(elevation) * math.sin(azimuth),
        math.sin(elevation),
    )


def pole_axis(side: str, pole: str):
    """The planet's own pole direction in the piece frame."""
    tilt = math.radians(P.lean_sign(side) * P.PLANETS[PLANET]["tilt"])
    sign = 1.0 if pole == "north" else -1.0
    return (sign * math.sin(tilt), 0.0, sign * math.cos(tilt))


def samples(shape):
    """Points on one body's own surface, in the piece frame."""
    points, _faces = shape.tessellate(TOLERANCE)
    return [(point.X, point.Y, point.Z) for point in points]


def facing_fraction(points, centre, axis) -> float:
    """What share of these points is on the hemisphere the camera can see."""
    seen = 0
    for x, y, z in points:
        dx, dy, dz = x - centre[0], y - centre[1], z - centre[2]
        if dx * axis[0] + dy * axis[1] + dz * axis[2] > 0.0:
            seen += 1
    return seen / max(len(points), 1)


def offset_fraction(points, centre, axis, radius) -> float:
    """How far the body's mean direction sits from the middle of the disc.

    0.00 is the dead centre of the visible face, 1.00 is the limb, above 1.00
    is past it.  Measured as the sine of the angle between the body's mean
    direction and the view axis, which is exactly where that direction lands in
    projection.
    """
    total = [0.0, 0.0, 0.0]
    for x, y, z in points:
        total[0] += x - centre[0]
        total[1] += y - centre[1]
        total[2] += z - centre[2]
    length = math.sqrt(sum(value * value for value in total))
    if length < 1e-9:
        return 0.0
    mean = [value / length for value in total]
    along = sum(mean[index] * axis[index] for index in range(3))
    along = max(-1.0, min(1.0, along))
    across = math.sqrt(max(1.0 - along * along, 0.0))
    return across if along >= 0.0 else 2.0 - across


def projected_radii(points, centre, axis):
    """Each point's distance from the piece's axis in the image plane.

    The camera looks along `-axis`, so a point's position in the picture is
    what is left of it after the component along `axis` is taken out.  This
    returns those lengths, which are what a reader sees as "how far out from
    the middle of the piece" -- for the ring, whether it clears the globe.
    """
    out = []
    for x, y, z in points:
        offset = (x - centre[0], y - centre[1], z - centre[2])
        along = sum(offset[i] * axis[i] for i in range(3))
        flat = [offset[i] - along * axis[i] for i in range(3)]
        out.append(math.sqrt(sum(value * value for value in flat)))
    return out


def image_plane(axis):
    """Two unit vectors square to the view axis, so a point can be placed in
    the picture rather than only measured away from its middle."""
    seed = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    right = (
        seed[1] * axis[2] - seed[2] * axis[1],
        seed[2] * axis[0] - seed[0] * axis[2],
        seed[0] * axis[1] - seed[1] * axis[0],
    )
    length = math.sqrt(sum(value * value for value in right))
    right = tuple(value / length for value in right)
    up = (
        axis[1] * right[2] - axis[2] * right[1],
        axis[2] * right[0] - axis[0] * right[2],
        axis[0] * right[1] - axis[1] * right[0],
    )
    return right, up


#: How finely the two footprints are compared, in millimetres of the picture.
#: Coarser than the sampling, so a cell is covered when material lands in it
#: rather than when a sample happens to.
FOOTPRINT_CELL = 0.5


def footprint(points, centre, axis):
    """The set of picture cells one body's visible surface covers."""
    right, up = image_plane(axis)
    cells = set()
    for x, y, z in points:
        offset = (x - centre[0], y - centre[1], z - centre[2])
        u = sum(offset[i] * right[i] for i in range(3))
        v = sum(offset[i] * up[i] for i in range(3))
        cells.add((round(u / FOOTPRINT_CELL), round(v / FOOTPRINT_CELL)))
    return cells


def visible_points(points, centre, axis):
    return [
        point for point in points
        if sum((point[i] - centre[i]) * axis[i] for i in range(3)) > 0.0
    ]


def main() -> int:
    centre = (0.0, 0.0, P.globe_centre_z(PLANET))
    radius = P.globe_radius(PLANET)
    hood_colour = MARKINGS[PLANET][0][1]

    print("# Which Uranus pole faces the camera")
    print()
    print("Measured on the exact colour bodies `parts/world.py` builds, sampled")
    print("on their own surfaces at %.2f mm and dotted against each canonical" % TOLERANCE)
    print("camera's view axis. Nothing here is read off a render.")
    print()
    print("Uranus's obliquity is %.2f degrees, which puts its pole %.2f degrees"
          % (P.PLANETS[PLANET]["tilt"], P.PLANETS[PLANET]["tilt"] - 90.0))
    print("past horizontal. A Sol world leans its north pole toward +X and its")
    print("Anti-Sol mirror toward -X, so the two armies show opposite poles.")
    print()
    print("## The poles themselves")
    print()
    print("| frame | army | north pole vs view axis | south pole vs view axis |")
    print("|---|---|---:|---:|")
    for label, view in FRAMES.items():
        axis = view_axis(*view)
        for side in P.SIDES:
            angles = []
            for pole in ("north", "south"):
                direction = pole_axis(side, pole)
                dot = sum(direction[i] * axis[i] for i in range(3))
                angles.append(math.degrees(math.acos(max(-1.0, min(1.0, dot)))))
            print("| %s | %s | %.1f deg | %.1f deg |"
                  % (label, side, angles[0], angles[1]))
    print()
    print("Under 90 degrees is on the visible face; over 90 is behind the limb.")
    print()
    print("## The hoods, as built")
    print()
    print("| frame | army | body | facing | pole offset | visible span | reads as |")
    print("|---|---|---|---:|---:|---|---|")
    failures = []
    bodies = {side: world_bodies(PLANET, side) for side in P.SIDES}
    points = {
        (side, role): samples(shape)
        for side, table in bodies.items()
        for role, (_colour, shape) in table.items()
        if role.startswith("hood") or role == "ring"
    }
    for label, view in FRAMES.items():
        axis = view_axis(*view)
        for side in P.SIDES:
            shown = 0
            for role in ("hood_north", "hood_south"):
                if (side, role) not in points:
                    continue
                seen = facing_fraction(points[(side, role)], centre, axis)
                where = offset_fraction(points[(side, role)], centre, axis, radius)
                seen_points = visible_points(points[(side, role)], centre, axis)
                if seen >= VISIBLE_FRACTION and seen_points:
                    shown += 1
                    radii = projected_radii(seen_points, centre, axis)
                    inner = min(radii) / radius
                    read = ("a broad region over the outer face, from %.2f of "
                            "the silhouette radius out to the limb" % inner)
                    span = "%.2f to %.2f" % (inner, max(radii) / radius)
                else:
                    read = "hidden behind the limb"
                    span = "--"
                print("| %s | %s | `%s` | %.0f%% | %.2f | %s | %s |"
                      % (label, side, role, 100.0 * seen, min(where, 2.0), span, read))
            if shown == 0:
                failures.append("%s shows no hood at the %s frame" % (side, label))
    print()
    print("Facing is the share of that body's own surface samples on the")
    print("hemisphere the camera can see. Pole offset is the sine of the angle")
    print("between the body's mean direction and the view axis: 0.00 is the dead")
    print("centre of the visible disc, 1.00 is the limb, above 1.00 is past it.")
    print("Visible span is where the part a reader can actually see lands in")
    print("projection, as a fraction of the globe's own radius.")
    print()
    print("**The hood is a broad region, not a spot, and it is not centred.**")
    print("The product's own two cameras are 60 to 62 degrees off this planet's")
    print("pole, so the visible hood runs from roughly half a radius out to the")
    print("limb: a wide soft brightening across the outer half of the face on the")
    print("side the piece leans toward. The centred reading the reference shows")
    print("is what the piece's own polar frame sees -- `snap/worlds/")
    print("uranus-sol-polar.png` and `uranus-anti-south-polar.png` -- and those")
    print("cameras sit 7.77 degrees below the horizon, which is the obliquity")
    print("rather than a choice. Both are rendered and both are kept.")
    print()
    print("## The ring against the hood")
    print()
    print("| frame | army | ring, visible span | ring outside the globe | visible hood span | hood cells the ring crosses |")
    print("|---|---|---|---:|---|---:|")
    overlap = []
    for label, view in FRAMES.items():
        axis = view_axis(*view)
        for side in P.SIDES:
            ring = visible_points(points[(side, "ring")], centre, axis)
            ring_r = [value / radius for value in projected_radii(ring, centre, axis)]
            outside = sum(1 for value in ring_r if value >= 1.0) / max(len(ring_r), 1)
            hood = []
            for role in ("hood_north", "hood_south"):
                seen_points = visible_points(points[(side, role)], centre, axis)
                if (facing_fraction(points[(side, role)], centre, axis)
                        >= VISIBLE_FRACTION and seen_points):
                    hood = [value / radius
                            for value in projected_radii(seen_points, centre, axis)]
            hood_cells = set()
            for role in ("hood_north", "hood_south"):
                seen_points = visible_points(points[(side, role)], centre, axis)
                if (facing_fraction(points[(side, role)], centre, axis)
                        >= VISIBLE_FRACTION and seen_points):
                    hood_cells |= footprint(seen_points, centre, axis)
            crossed = len(hood_cells & footprint(ring, centre, axis))
            share = crossed / max(len(hood_cells), 1)
            print("| %s | %s | %.2f to %.2f | %.0f%% | %.2f to %.2f | %.0f%% |"
                  % (label, side, min(ring_r), max(ring_r), 100.0 * outside,
                     min(hood), max(hood), 100.0 * share))
            overlap.append((label, side, share, outside))
    print()
    worst = max(share for _l, _s, share, _o in overlap)
    outsides = [value for _l, _s, _share, value in overlap]
    print()
    print("A ring lies in the planet's equatorial plane, which is square to the")
    print("pole, so in space the hoop is 90 degrees from the hood everywhere and")
    print("the two cannot touch. What is left to check is the picture, where a")
    print("near limb can still cross in front of something behind it, and that is")
    print("the last column: the share of the picture cells the visible hood covers")
    print("that the visible ring also covers, at %.1f mm of picture per cell."
          % FOOTPRINT_CELL)
    print()
    if worst <= 0.0:
        print("**The hoop crosses none of the visible hood, at either frame, on")
        print("either army.** Not a small share -- none. The hoop is a narrow")
        print("upright band running over the meridian square to the pole, and the")
        print("hood is a wide region filling the outer face on the side the piece")
        print("leans toward, so the chord the hoop draws falls clear of it. They")
        print("occupy different parts of the piece, **checked rather than")
        print("assumed**, which is what the correction asked for.")
    else:
        print("**The worst case is %.0f per cent, at %s on the %s piece.**"
              % (100.0 * worst,
                 *next((label, side) for label, side, share, _o in overlap
                       if share == worst)))
        print("The hoop is a narrow upright band crossing the face on one chord and")
        print("the hood is a wide region on the outer face; they share that much")
        print("and nothing more.")
    print()
    print("Between %.0f and %.0f per cent of the visible hoop stands outside the"
          % (100.0 * min(outsides), 100.0 * max(outsides)))
    print("globe's own silhouette. That is the part that reads as a ring standing")
    print("off the ball rather than as a line drawn on it; the rest is the near")
    print("limb of the same hoop seen against the globe behind it. On a hoop this")
    print("small -- 1.00 mm of projection on an 11.01 mm radius -- that is what")
    print("a ring seen from anywhere but down its own axis looks like, and the")
    print("frame that shows the whole circle is the piece's own polar one.")
    print()
    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("**Every army shows a hood at every photographed frame.** That is")
        print("not what a single northern hood would have done, and measuring it")
        print("is what put a hood on both poles: with north alone, the Anti-Sol")
        print("piece turns its only marking 125.3 degrees from the camera at the")
        print("hero frame and 130.5 at the sheet frame -- past the limb at both,")
        print("so a whole army would have carried a marking no player ever sees.")
        print("Two hoods is also what the planet has. Uranus points a pole at the")
        print("Sun for forty years at a time and the bright polar region follows")
        print("whichever pole that is, so over one orbit it is both.")
    print()
    print("## What two hoods cost, said rather than hidden")
    print()
    print("A hood at each pole makes this world's SURFACE symmetric, so at the")
    print("product's own two frames the two armies show the same thing: a pale")
    print("region on the same side of the globe and the hoop across the other.")
    print("`snap/worlds/uranus-pair-hero.png` shows exactly that. On Saturn the")
    print("single northern cap is an ownership cue in its own right --")
    print("`measure/saturn-cap-visibility.md` makes that case -- and Uranus gives")
    print("that up.")
    print()
    print("It gives it up for a reason and not for nothing. A northern hood alone")
    print("is not a cue on this world, it is a marking one army never shows: the")
    print("numbers above put it 125.3 and 130.5 degrees from the camera on every")
    print("Anti-Sol piece, past the limb at both frames. A cue that is invisible on")
    print("half the pieces is not a cue. What still tells the two apart on this")
    print("world is what tells them apart on the six worlds with no cap at all --")
    print("the disc, `white` against `black`, and the numeral in the other tone --")
    print("plus one thing those six do not have: the hoop leans the other way,")
    print("because it stands in the equatorial plane of a globe that leans the")
    print("other way. `measure/uranus-mirror.md` measures that as an exact mirror")
    print("in X.")
    print()
    print("The hoods print in `%s`; `measure/uranus-tone-separation.md` is why."
          % hood_colour)
    print("Measured by `measure/uranus_facing.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
