"""Neptune's three white cloud bands, its Great Dark Spot, and the spot's
bright companion cloud.

Neptune wears three closed white latitude bands at -46/-41, 11/15 and 30/33,
one dark oval, and -- new in this revision -- one small white oval just south
of that dark oval.  The bands and the spot are carried forward from the build
this revision corrects without a digit changed.  The companion is the only
thing added, and it is the only thing this module's numbers move for.

**The bands are here by owner decision, not by measurement, and that decision
is not reopened.**  An earlier correction removed them, made a real case for
removing them -- `ref/neptune-sol.png` shows clouds that are SHORT, tilted,
scattered and not one of them circling the planet, and three closed bands on a
blue ball read as three painted stripes -- and the owner looked at both
drawings and kept the bands.  That losing argument is preserved word for word
in `parts/markings.py` under `"neptune"`.  Nothing here softens, narrows,
moves or breaks the bands, and nothing here is an occasion to revisit them:
this revision adds one oval and touches nothing else.

**The companion cloud is what this revision adds.**  The archived build that
the bands reversed had one -- a white wisp drawn parallel to the spot's upper
rim -- and reverting the cloud family to three bands took it with it.  The
sealed report said so in as many words: "`ref/neptune-sol.png` does show a
bright companion cloud beside the dark spot and this revision does not draw
one.  That is a deliberate loss."  The owner has now asked for it back, on
both Neptune pieces, as ONE WHITE OUTLINE OVAL about 10 by 5 degrees of arc,
at the spot's own longitude, south of it.

It is drawn here rather than in the white band marking, under its own key, for
the reason the archived build's note gives against itself: a companion that
lives inside the cloud family disappears whenever the cloud family is
redrawn.  `companion` is its own marking with its own key, so the next person
to argue about bands cannot delete it by accident.

**Where it sits: exactly where it was asked for, and what that costs.**  Its
centre is 8.0 degrees of latitude south of the spot's centre, at the spot's own
longitude, which is the instruction.  Drawing it there is not free and the cost
is recorded here rather than discovered later.

The spot is 14 degrees of arc tall, so its own southern rim is already 7
degrees south of its centre, and an oval 5 degrees tall centred at 8 puts its
top 1.5 degrees INSIDE the spot.  The obvious answer is to move it further
south until a printable strip of bare globe fits between the two outlines,
which needs 11.59 degrees.  **That answer was built, rendered and rejected on
the evidence.**  `parts/world.py` seats every globe on a cone that springs at
piece-frame latitude -42, and the planet leans 28.32 degrees, so at the spot's
own longitude the Sol piece's seat collar covers everything south of about
-31 degrees of PLANET latitude.  At 11.8 degrees south the oval's centre lands
at piece latitude -40.9 and ten of its twenty-four ring vertices fall under the
collar: the Sol piece came back with a pale half-lens sitting on its base
instead of an oval.  The window between the spot's southern rim and that collar
is about 2.4 degrees of arc, 0.46 mm, and a marking plus two nozzle-width gaps
does not fit in 0.46 mm at any size.  The scan is in
`measure/neptune-atlas-resolution.md`: at every half-axis from 0.8 to 2.4
degrees there is no latitude that clears both.

So the instruction's own number is kept and the overlap is resolved by cutting
the spot back -- but NOT back to the companion itself.  That was built first:
`spot` subtracted `companion`, the two colours shared a boundary, and an
independent reader shown the finished renders cold called the pair "a notched
figure-eight" and the new marking "a small grey circle", a lobe budding off the
dark spot rather than a cloud beside it.  The figure the owner asked for came
out inverted.

**So the spot is cut to a KEEP-OUT: the companion's own oval grown by 2.30
degrees of arc, a shape that is never drawn and never printed.**  What survives
between the two markings is bare blue, 0.42 mm of it at the closest point --
1.05 nozzle widths, and one nozzle width is the least this set will print a
colour boundary at.
The dilation is solved rather than guessed: the offset of an ellipse is not an
ellipse, so growing both half-axes by one nozzle leaves the two curves closer
than a nozzle somewhere in between, and 2.19 is only where the two RINGS reach
0.40 mm apart -- measured against where the DARK actually stops it lands at
0.3995, a rounding under. 2.30 is the first round tenth above that and measures
0.4203 mm.
`parts/world._subtrahend` is the one line of machinery that makes a never-drawn
subtraction possible, and it exists for this.

**What that costs the dark spot, and it is the largest thing this revision does
to anything it was told not to change.**  The keep-out is 14.6 by 9.6 degrees
of arc against the companion's 10 by 5, so where it crosses the spot it takes a
bay about 15 degrees of arc wide and 3.7 deep out of a 28 by 14 oval: the
`spot` body falls from the archive's 11.9319 mm3 to 10.5113, a loss of 1.4206.
The spot's RING is not edited -- its latitude, longitude, half-axes, 40
vertices and `dark_gray` filament are byte-identical in the source, and
`measure/neptune-facing.md` reproduces its archived dot products at every frame
-- and `measure/neptune-mirror.md` measures the spot's own region BEFORE the
cut at the archive's exact 11.9319 and accounts every cubic millimetre of the
difference to the keep-out.  What changed is where the dark stops, not where
the spot is.

That is the whole trade, stated so a reader can disagree with it: the owner
asked for a bright cloud just south of the Great Dark Spot and said nothing
else on the piece changes.  At 8 degrees on a spot 14 degrees tall those two
cannot both hold.  A cloud that touches the spot keeps the spot's outline and
loses the cloud -- a reader who had never seen the brief saw a lump, not a
companion.  A cloud held one nozzle clear delivers the cloud and costs the spot
a bay.  The cloud is what was asked for, so the cloud wins, and the bay is
disclosed here, in `antisol_spec.md` item 26 and in the product's limitations
rather than left to be found.

Two things are drawn here, and one piece of arithmetic decides all three.
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

**The dark spot does not move, and nothing in this revision asks it to.**  It
was two overlapping `blob` circles at -22 and -20 two builds ago and read as a
smudge; the reference shows a clean oval about twice as wide as it is tall.
Neptune's Great Dark Spot was about 13000 by 6600 km on a planet 49244 km
across, so one degree of arc is 429.7 km and the spot is 30.3 by 15.4 degrees
-- taken here as 28 by 14, the exact 2:1 that correction asked for and within
8 per cent of the measured object.  Its ring, its 40 vertices, its latitude,
its longitude and its `dark_gray` filament are carried forward unchanged, and
`measure/neptune-mirror.md` measures its built body against the volume the
archive recorded rather than assuming it did not move.

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


# ------------------------------------------------------- the companion ---
#: The companion's own half-axes, in degrees of great-circle arc.  The owner
#: asked for an oval "about 10 by 5 degrees of arc", which is the same way the
#: spot's size is stated above -- 28 by 14 there, half-axes 14 and 7 -- so 10
#: by 5 is the whole oval and these are half of it.
#:
#: 5 degrees of arc is 0.955 mm on this globe, 2.39 nozzle widths, and it is
#: the narrowest the white material ever gets: an ellipse's narrowest neck is
#: its own minor axis.  That is the limit the owner's instruction names, and
#: `measure/neptune-atlas-resolution.md` measures it on the walked ring rather
#: than trusting this comment.
COMPANION_SEMI_ARC_LON = 5.0
COMPANION_SEMI_ARC_LAT = 2.5

#: Degrees of latitude from the spot's centre down to the companion's centre.
#:
#: 8.0 is the owner's own number and it is kept.  It is not a free choice and
#: it is not a comfortable one: the spot's half-height is 7.0 and the
#: companion's is 2.5, so at 8.0 the two ovals OVERLAP by 1.5 degrees.  The
#: module docstring carries the scan that shows no other offset works -- south
#: of about 9 degrees the Sol piece's seat collar starts eating the oval, and a
#: printable strip of bare globe between the two outlines needs 11.59 -- so the
#: overlap is resolved by subtraction rather than by moving the marking.
#: `parts/markings.py` gives `spot` a `("companion",)` subtraction.
COMPANION_OFFSET_ARC = 8.0

#: Latitude and longitude of the companion's centre.
#:
#: The longitude is the spot's own, exactly as asked.  It is free in the
#: absolute -- Neptune turns in sixteen hours and this set fixes no meridian --
#: but it is not free RELATIVE to the spot, and the instruction fixes it.
COMPANION_LAT = SPOT_LAT - COMPANION_OFFSET_ARC
COMPANION_LON = SPOT_LON

#: The companion's vertex count, set by the same test the spot's 40 was set by
#: rather than copied from it.  An ellipse walked at even bearings is furthest
#: from the true curve at its two pointed ends, and that error falls as the
#: square of the count and rises with the size of the oval.  The spot is 28
#: degrees of arc long at 40 vertices and its ends fall 0.017 mm inside the
#: true ellipse, which is the figure an independent reader's faceting
#: complaint was answered at.  This oval is 10 degrees long, 0.357 times the
#: spot, so 24 vertices buy the same smoothness at a coarser count.  Measured
#: in `measure/neptune-atlas-resolution.md`, which walks both rings and takes
#: the worst departure of a chord from the true ellipse: the spot at 40
#: vertices falls 0.031 mm inside it and this oval at 24 falls 0.028 mm
#: inside.  The shortest edge that leaves is 0.127 mm, against the 0.075 mm
#: copying 40 across would have left, and like the spot's own 0.21 mm it is a
#: facet of a smooth curve rather than the width of anything.
COMPANION_VERTICES = 24

COMPANION_RING = oval_ring(COMPANION_LAT, COMPANION_LON,
                           COMPANION_SEMI_ARC_LON, COMPANION_SEMI_ARC_LAT,
                           COMPANION_VERTICES)


#: How far the dark spot is held back from the companion, in degrees of arc.
#:
#: NOT the companion's own size: this is the KEEP-OUT the spot is cut to, so a
#: printable strip of bare blue survives between the two outlines instead of
#: the two colours sharing a boundary.
#:
#: 2.30 is solved rather than chosen.  The offset of an ellipse is not an
#: ellipse, so growing both half-axes by one nozzle width leaves the two curves
#: closer than a nozzle somewhere in between: 2.19 is where the two RINGS first
#: reach 0.40 mm apart, and it is not enough, because what a reader and a
#: slicer see is the distance to where the DARK STOPS -- the spot's own ring
#: outside the keep-out, plus the keep-out's ring inside the spot -- walked at
#: a finite step.  Measured that way 2.19 lands at 0.3995 mm, a rounding under
#: the nozzle.  2.30 is the first round tenth above it and measures 0.42 mm.
#: `measure/neptune-atlas-resolution.md` re-measures it on the built rings
#: rather than trusting this comment.
COMPANION_KEEPOUT_ARC = 2.30

#: The keep-out ring itself.  It is never drawn and never printed: no body in
#: this set has its shape.  40 vertices rather than the companion's 24 because
#: it is a boundary of the DARK spot, which is the larger body and is held to
#: the spot's own smoothness.
COMPANION_KEEPOUT_RING = oval_ring(
    COMPANION_LAT, COMPANION_LON,
    COMPANION_SEMI_ARC_LON + COMPANION_KEEPOUT_ARC,
    COMPANION_SEMI_ARC_LAT + COMPANION_KEEPOUT_ARC, 40)


def companion_keepout_spec():
    """The region `parts/markings.py` cuts out of the `spot` marking.

    Handed over as a `("spec", ...)` subtraction rather than as a marking key,
    because nothing is printed here: it is the bare globe the companion needs
    around it so that the white and the dark never meet.
    """
    return ("spec", ("outline", [COMPANION_KEEPOUT_RING]))


def companion_specs():
    """The region specs `parts/markings.py` gives the `companion` marking.

    One `outline` oval, the same region kind and the same construction the
    spot uses, in `white` rather than `dark_gray`.  It subtracts nothing and
    nothing subtracts it: it stands clear of every other marking on this globe
    by more than a nozzle width, which is the whole reason it sits where it
    sits.
    """
    return [("outline", [COMPANION_RING])]


# ------------------------------------------------------------ the record --
#: name -> ring, for the resolution report.  The spot and the companion are
#: the two outlines on this globe; the three bands are circles of latitude and
#: are measured from `BANDS`.
RINGS = {"spot": SPOT_RING, "companion": COMPANION_RING}

NOT_DRAWN = (
    "Neptune's globe is \u00d8%.2f mm, so one degree of arc is %.4f mm and a "
    "%.1f mm nozzle is %.2f degrees of it. DRAWN, and new in this revision: "
    "the dark spot's BRIGHT COMPANION CLOUD, one white oval %.0f by %.0f "
    "degrees of arc at the spot's own longitude, %.1f degrees of latitude "
    "south of the spot's centre, which overlaps the spot's southern rim by "
    "1.5 degrees and takes a scallop out of it by subtraction rather than "
    "moving south, because south of about 9 degrees the Sol piece's seat "
    "collar covers the oval. Considered and refused: a "
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
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG,
       2 * COMPANION_SEMI_ARC_LON, 2 * COMPANION_SEMI_ARC_LAT,
       SPOT_LAT - COMPANION_LAT)
)
