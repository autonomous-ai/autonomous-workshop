"""Neptune's three white cloud bands and its Great Dark Spot.

Neptune wears three closed white latitude bands at -46/-41, 11/15 and 30/33,
and one dark oval.  That is what it wore before the cloud correction of
2026-09-19 and it is what it wears again.

**The bands came back by owner decision, not by measurement.**  The correction
that removed them made a real case and made it well: `ref/neptune-sol.png`
shows clouds that are SHORT -- each starts and stops inside a few tens of
degrees of longitude, they sit at slightly different angles to the parallel,
they are scattered across the face rather than ringing it, and not one of them
circles the planet -- and three closed bands on a blue ball read as three
painted stripes, the most beach-ball-like object in the set.  It replaced them
with eight tapered, bowed, tilted streaks and a bright companion wisp beside
the spot, and an independent reader confirmed the beach ball had gone.

The owner has since looked at both and prefers the older drawing.  That case
was heard and overruled; it is kept in full in `parts/markings.py` under
`"neptune"` so that a reader can see the losing argument rather than a summary
of it.  Nothing here softens, narrows, moves or breaks the bands to make the
beach-ball reading come out better: three closed bands at those three
latitudes is the instruction, and the reading they produce is recorded next to
the decision rather than engineered away.

Two things are drawn here, and one piece of arithmetic decides both.
Neptune's globe is Ø21.89 mm, so its radius is 10.945 mm, one degree of
GREAT-CIRCLE arc is pi * 21.89 / 360 = 0.1910 mm, and the 0.40 mm nozzle is
2.09 degrees of it.  That factor is pi * d / 360, NOT pi * d / 180: a full
great circle is pi * d long and 360 degrees round.  This chain has put the
doubled figure into a sealed archive once already, so it is derived here in
the open and `measure/neptune-atlas-resolution.md` measures every width, gap
and neck against the nozzle on the exact numbers this module hands the build.

**The bands are three plain `band` regions, one marking, one key.**  A `band`
is the region kind `features/patches.latitude_band_tool` draws: a torus that
meets the globe's own sphere exactly at the band's two edge latitudes, so a
band declared 5 degrees wide is 5 degrees of arc wide on the printed surface,
at every longitude, and dips to `RELIEF_DEPTH` at its own middle.  No outline
ring, no taper, no bow, no tilt, no end cap -- a closed circle of latitude has
none of those.

**The dark spot does not move, and this is the one decision of the cloud
correction that stands.**  It was two overlapping `blob` circles at -22 and
-20 before that correction and read as a smudge; the reference shows a clean
oval about twice as wide as it is tall.  Neptune's Great Dark Spot was about
13000 by 6600 km on a planet 49244 km across, so one degree of arc is 429.7 km
and the spot is 30.3 by 15.4 degrees -- taken here as 28 by 14, the exact 2:1
the correction asked for and within 8 per cent of the measured object.  Its
latitude, -22, is the real one; its longitude is free, because Neptune turns
in sixteen hours and this set fixes no meridian.  Its ring, its 40 vertices,
its latitude, its longitude and its `dark_gray` filament are carried forward
unchanged, and `measure/neptune-atlas-resolution.md` measures its own
contribution rather than assuming it did not move.

**The spot's bright companion is back, as its own small oval (correction of
2026-09-26).**  The previous revision dropped the white wisp that used to lie
along the spot's upper rim, because it lived in the white cloud marking the
owner reverted to three bands.  `ref/neptune-sol.png` does show a bright
companion cloud beside the dark spot, and the owner now asks for it: one
white outline oval, about 10 by 5 degrees of arc, centred about 8 degrees of
latitude south of the spot's centre and at the same longitude, inside the
narrowest-feature limit the set already uses for printable markings.

Those numbers cannot all hold exactly, and two measurements decide which give.

First, the spot.  Its semi-minor axis is 7 degrees, so its southern rim is at
-29 on its own meridian; a 5-degree-tall companion centred 8 degrees south of
-22 would reach from -32.5 up to -27.5 and overlap the spot by 1.5 degrees.
Because the spot is listed first it would trim the companion into a crescent
whose horns run down to zero width, and even a tangent touch leaves a wedge of
bare blue that narrows to nothing -- colour boundaries finer than the 0.40 mm
nozzle this set holds every marking and every bare gap to.

Second, the seat.  The seat cone springs from the sphere at latitude -42 about
the PIECE's vertical, and Neptune's 28.32-degree lean carries the southern
hemisphere at the spot's longitude down toward it on the Sol army: the spot's
own southern rim already sits at piece latitude -40 there.  The first build of
this correction put the companion at -34.5 on the spot's own meridian, and 41%
of it lay under the seat on the Sol piece -- an independent blind reader saw
"a sliver" of it above the collar and called that blocking, rightly.

So the companion is centred at latitude -33.5, 11.5 degrees south of the
spot's centre, and 10 degrees of longitude WEST of the spot's centre, at -75.2.
That is still under the spot -- the spot spans 14 degrees either side of its
centre -- so it reads as the small cloud just south of the dark spot, a little
toward its western end.  At that place its nearest approach to the spot's rim
is 3.07 degrees of arc (0.587 mm at the surface, more than the 2.35 degrees a
0.40 mm gap needs at the 1.20 mm inlay floor), and its lowest point on the Sol
piece is at piece latitude -39.4, 2.6 degrees clear of the seat.  It is the
least longitude shift that satisfies both: a grid search over offset and
latitude found none at a smaller offset.  Both armies use this one
description, so the two pieces stay each other's mirror.  The `b1` band's
northern edge at -41 is 5 degrees below the companion's southern rim.

It is its own marking, `companion`, in the `white` filament the bands use,
listed after the spot and the bands so it is trimmed by neither and
subtracts from neither: the spot's ring, the three bands and the globe's
other bodies are built exactly as before, and `measure/neptune-companion.md`
checks that on the built bodies rather than asserting it.

Nothing else is on this globe.  `NOT_DRAWN` below carries what was considered
and refused, and why.
"""

from __future__ import annotations

import math

import params as P

#: The globe these features are drawn for, and what one degree of it is worth.
#:
#: `math.radians(1.0) * radius` IS `pi * diameter / 360`, written the way the
#: rest of this project writes an arc length.  The doubled form, `pi * d / 180`,
#: is the error requirement 4 of this revision names by hand; it is not used
#: here and no figure in this module or its report is derived from it.
GLOBE_D = P.globe_diameter("neptune")                 # 21.89 mm
GLOBE_R = GLOBE_D / 2.0                               # 10.945 mm
MM_PER_DEG = math.radians(1.0) * GLOBE_R              # 0.1910 mm
NOZZLE_DEG = P.NOZZLE_MM / MM_PER_DEG                 # 2.09 degrees of arc

#: Neptune's real equatorial diameter, and the kilometres one degree of arc on
#: it is worth.  This is the arithmetic the spot's size comes from.
DIAMETER_KM = P.PLANETS["neptune"]["d_km"]            # 49244 km
KM_PER_DEG = math.pi * DIAMETER_KM / 360.0            # 429.7 km


# ------------------------------------------------------------ vector maths ---
def _unit(lon_deg: float, lat_deg: float) -> tuple[float, float, float]:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def _lon_lat(vector) -> tuple[float, float]:
    x, y, z = vector
    return (math.degrees(math.atan2(y, x)),
            math.degrees(math.asin(max(-1.0, min(1.0, z)))))


def _cross(one, other):
    return (one[1] * other[2] - one[2] * other[1],
            one[2] * other[0] - one[0] * other[2],
            one[0] * other[1] - one[1] * other[0])


def _dot(one, other):
    return one[0] * other[0] + one[1] * other[1] + one[2] * other[2]


def _normalise(vector):
    length = math.sqrt(_dot(vector, vector))
    return tuple(value / length for value in vector)


def _combine(*terms):
    """sum(scale * vector) over (scale, vector) pairs."""
    return tuple(sum(scale * vector[axis] for scale, vector in terms)
                 for axis in range(3))


# ------------------------------------------------------- the three bands ---
#: (key, southern edge, northern edge), in degrees of latitude.
#:
#: These three pairs are the ones the build carried before the cloud
#: correction, restored verbatim.  They were read back off the source's own
#: record of what it replaced -- the comment in `parts/markings.py` that
#: quotes them as "-46/-41, 11/15 and 30/33" -- rather than taken from the
#: revision brief, and the two agree.
#:
#: Widths of 5, 4 and 3 degrees of arc, which is 0.955, 0.764 and 0.573 mm on
#: this globe.  The narrowest is 1.43 nozzle widths, so none of them needed
#: widening and none was widened; `measure/neptune-atlas-resolution.md`
#: measures each one and the bare gaps between them.
BANDS = (
    ("b1", -46, -41),
    ("b2",  11,  15),
    ("b3",  30,  33),
)


def band_specs():
    """The region specs `parts/markings.py` gives the `bands` marking.

    Three plain `band` regions in one marking with one key and one filament,
    exactly as they stood before the cloud correction.  `parts/world.py` clips
    each one separately and carries the remainder forward, so the three come
    back as three disjoint bodies of one colour.
    """
    return [("band", low, high) for _key, low, high in BANDS]


def band_width_deg(key: str) -> float:
    for name, low, high in BANDS:
        if name == key:
            return float(high - low)
    raise KeyError(key)


# ------------------------------------------------------------- the spot ---
def oval_ring(lat_deg: float, lon_deg: float, semi_lon: float, semi_lat: float,
              count: int) -> list[tuple[float, float]]:
    """A closed oval on the sphere, `semi_lon` by `semi_lat` degrees of arc.

    The same construction `parts/jupiter_atlas.oval_ring` draws the Great Red
    Spot with, reproduced here rather than imported so that a change to
    Jupiter's spot cannot silently move Neptune's: the angular radius at
    bearing theta from north is `a b / sqrt((b sin t)^2 + (a cos t)^2)`, which
    is an ellipse in polar form.  Both semi-axes are degrees of great-circle
    arc, so the oval is the size it says it is at the latitude it sits at.
    """
    centre = _unit(lon_deg, lat_deg)
    east = _normalise(_cross((0.0, 0.0, 1.0), centre))
    up = _cross(centre, east)
    ring = []
    for index in range(count):
        theta = -2.0 * math.pi * index / count
        radius = (semi_lon * semi_lat
                  / math.hypot(semi_lat * math.sin(theta),
                               semi_lon * math.cos(theta)))
        reach = math.radians(radius)
        point = _combine(
            (math.cos(reach), centre),
            (math.sin(reach) * math.cos(theta), up),
            (math.sin(reach) * math.sin(theta), east),
        )
        lon, lat = _lon_lat(point)
        ring.append((round(lon, 4), round(lat, 4)))
    return ring


#: 13000 by 6600 km at 429.7 km per degree of arc is 30.3 by 15.4 degrees,
#: taken as 28 by 14: the exact 2:1 the correction asked for, within 8 per
#: cent of the measured object.  Semi-axes, in degrees of great-circle arc.
#:
#: Every value below is carried from the build this revision corrects, without
#: a digit changed.  The owner's instruction is that the dark spot does not
#: move, and the check that it did not is the spot's own STEP contribution in
#: `measure/neptune-atlas-resolution.md` rather than this comment.
SPOT_LAT = -22.0
SPOT_LON = -65.2
SPOT_SEMI_ARC_LON = 14.0
SPOT_SEMI_ARC_LAT = 7.0

#: The spot's vertex count.  40 rather than the 22 the first build of the oval
#: used, and that was a repair: an independent reader of the 22-vertex oval
#: reported "straight facets and corners on its lower left ... a low-polygon
#: shape rather than an oval", which is precisely what replacing two
#: overlapping circles was meant to avoid.  An ellipse walked at even bearings
#: puts its samples furthest apart at the two pointed ends, so the count has to
#: be set by the ends rather than by the average: at 22 the end chord fell
#: 0.055 mm inside the true ellipse and at 40 it falls 0.017 mm inside, a
#: twelfth of a nozzle.  The shortest edge drops to about 0.21 mm, which is a
#: facet of a curve rather than the width of anything -- the spot's own
#: narrowest neck stays its 2.67 mm minor axis, and
#: `measure/neptune-atlas-resolution.md` measures that rather than inferring it.
SPOT_VERTICES = 40

SPOT_RING = oval_ring(SPOT_LAT, SPOT_LON, SPOT_SEMI_ARC_LON,
                      SPOT_SEMI_ARC_LAT, SPOT_VERTICES)


def spot_specs():
    """The region specs `parts/markings.py` gives the `spot` marking."""
    return [("outline", [SPOT_RING])]


# -------------------------------------------------------- the companion ---
#: 10 by 5 degrees of arc, as the owner asked: semi-axes of 5 and 2.5, which
#: on this globe is 1.91 by 0.955 mm.  Its minor axis is its narrowest
#: neck and is 2.39 nozzle widths.
COMPANION_SEMI_ARC_LON = 5.0
COMPANION_SEMI_ARC_LAT = 2.5

#: Latitude -33.5, 11.5 degrees south of the spot's centre rather than the 8
#: the owner gave as "about" (8 would overlap the spot's rim), and longitude
#: 10 degrees west of the spot's centre rather than on it (on it, 41% of the
#: oval lies under the Sol piece's seat cone).  See the module docstring;
#: `measure/neptune-companion.md` measures the gap and the seat clearance on
#: the built bodies.
COMPANION_LON_OFFSET_DEG = -10.0
COMPANION_LON = SPOT_LON + COMPANION_LON_OFFSET_DEG          # -75.2
COMPANION_LAT = -33.5

#: 32 vertices.  Both rings are inscribed in their ellipses, so every chord
#: lies inside its own oval and can only widen the gap.
COMPANION_VERTICES = 32

COMPANION_RING = oval_ring(COMPANION_LAT, COMPANION_LON,
                           COMPANION_SEMI_ARC_LON, COMPANION_SEMI_ARC_LAT,
                           COMPANION_VERTICES)


def companion_specs():
    """The region specs `parts/markings.py` gives the `companion` marking."""
    return [("outline", [COMPANION_RING])]


# ------------------------------------------------------------ the record --
#: name -> ring, for the resolution report.  The spot and its companion are
#: outlines; the three bands are circles of latitude measured from `BANDS`.
RINGS = {"spot": SPOT_RING, "companion": COMPANION_RING}

NOT_DRAWN = (
    "Neptune's globe is Ø%.2f mm, so one degree of arc is %.4f mm and a "
    "%.1f mm nozzle is %.2f degrees of it. The spot's "
    "bright companion cloud IS drawn, as its own white oval. Considered and "
    "refused: a "
    "SECOND DARK SPOT -- the reference shows one; POLAR BRIGHTENING -- the "
    "reference shows none, and a bright cap on this globe would repeat "
    "Saturn's northern cap on the world two ranks below it; RING ARCS -- "
    "Neptune has rings, the reference does not show them, this set does not "
    "draw them, and a ring on rank 5 would collide with Saturn's role at "
    "rank 7 in the size ladder, where the ring IS the rank; a FAINT DARKER "
    "CENTRE inside the dark spot, which the reference shows and which would "
    "need a fourth filament on a globe held to three; and the reference's "
    "own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm here, under "
    "one nozzle width, and would print as noise. The set's material rules "
    "forbid deliberate grit."
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG)
)
