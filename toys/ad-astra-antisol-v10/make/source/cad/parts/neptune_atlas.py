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

**The spot's bright companion is gone, and that is a loss rather than a
tidy-up.**  It was a white wisp drawn parallel to the spot's upper rim at a
constant 0.60 mm clearance, and it lived in the white cloud marking rather
than beside the spot, because the marking key in this set is the filament.
Reverting the cloud family to three bands takes it with it, and the drawing
the owner is reverting to did not have one.  `ref/neptune-sol.png` does show a
bright companion cloud beside the dark spot and this revision does not draw
one.  That is recorded in the product's limitations in those terms.

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


# ------------------------------------------------------------ the record --
#: name -> ring, for the resolution report.  Only the spot is an outline now;
#: the three bands are circles of latitude and are measured from `BANDS`.
RINGS = {"spot": SPOT_RING}

NOT_DRAWN = (
    "Neptune's globe is Ø%.2f mm, so one degree of arc is %.4f mm and a "
    "%.1f mm nozzle is %.2f degrees of it. Considered and refused: the "
    "SPOT'S BRIGHT COMPANION CLOUD -- the reference shows one and the build "
    "this revision corrects drew one, and it is dropped here because it lived "
    "in the white cloud marking and the owner has reverted that marking to "
    "the three latitude bands it was before, which had no companion; it is a "
    "deliberate loss and the product's limitations say so. Also refused: a "
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
