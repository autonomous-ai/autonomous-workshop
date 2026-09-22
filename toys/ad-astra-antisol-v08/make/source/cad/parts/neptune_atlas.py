"""Neptune's cloud streaks, its Great Dark Spot and the spot's bright companion.

Neptune used to wear three closed `band` regions of `white` at -46/-41, 11/15
and 30/33.  A closed latitude band runs the whole way round the planet, so on
the finished piece those read as three painted stripes on a blue ball, and in
the whole-set render the two Neptunes were the most beach-ball-like objects in
the set.  `ref/neptune-sol.png` and `ref/neptune-anti.png` show something else
entirely: the white clouds are SHORT.  Each is a wisp that starts and stops
inside a few tens of degrees of longitude, they sit at slightly different
angles to the parallel, they are scattered across the face rather than ringing
it, and not one of them circles the planet.

Three things are drawn here, and one piece of arithmetic decides all three.
Neptune's globe is Ø21.89 mm, so its radius is 10.945 mm, one degree of
great-circle arc is 0.1910 mm, and the 0.40 mm nozzle is 2.09 degrees of it.
`measure/neptune-atlas-resolution.md` is the measurement; every number below is
checked against it on the exact rings this module hands the build.

**A streak is a closed outline ring, not a new kind of region.**  No new region
kind was needed.  An arc is a long thin closed ring running along a parallel,
and `features/patches.outline_tool` -- the outline machinery the Earth
correction built and Mercury, Mars, Venus, Jupiter and Saturn have used since
-- draws it directly as a radial prism through that ring.  `streak_ring` below
walks the ring: down one side of a great-circle centreline, round a
semicircular cap at the far end, back up the other side, and round the cap at
the near end.  The caps are why the ends are rounded rather than square cut: a
square end is the single thing that makes a short band read as a broken band
rather than as a cloud.

**The streaks are 1.5 mm wide, and that is an owner decision recorded on
2026-09-19 rather than a derivation.**  The arithmetic, in full, because it
overrules what an earlier version of this brief said.  The nozzle is 0.40 mm,
so a streak must be at least 2.09 degrees of arc to print at all and nearer 3
for the colour boundary not to be a single bead.  An earlier run drew them at
0.50 to 0.69 mm on exactly that reasoning; it was right about printing and
wrong about seeing.  At that width a streak is under two pixels in `iso.png`
and Neptune becomes the one world in the set whose surface does nothing at the
scale the set is actually looked at.  The rest of the set is not thin --
Saturn's bands are 3.63 to 7.26 mm and Jupiter's belts 2.35 to 6.12 mm -- so
1.5 mm is still the narrowest marking family anywhere in this set by a factor
of 1.6, and at 33 to 86 degrees of arc long it is 5:1 to 11:1 longer than it is
wide.  A streak, not a band.

THE COST, WHICH IS REAL.  The reference's own clouds scale to 0.13 - 0.26 mm on
this globe.  At 1.5 mm these are six to twelve times the reference width.  That
is a large, deliberate departure from the reference, taken by the owner with
those numbers in front of them, choosing legibility at the set's own viewing
scale over fidelity of width.  It is recorded in the product's limitations in
exactly those terms, and nothing here drifts back toward the nozzle to make the
number look better.

ONE ARITHMETIC CORRECTION, MADE IN THE OPEN.  The brief states the width twice,
once in millimetres and once in degrees, and the two do not agree: it gives
0.191 mm per degree of arc, which is right for this Ø21.89 mm globe, and then
calls 1.5 mm "3.93 degrees of arc", which is what 0.75 mm is.  The same factor
of two runs through its 7:1 and 23:1 aspect ratios.  The millimetre is what the
printer, the eye and the comparison against Saturn's and Jupiter's belts are
all in, and the instruction is stated in millimetres three times -- "DRAW THE
STREAKS 1.5 MM WIDE", "keep the family near 1.5 mm", "six to twelve times the
reference width", which is only true of 1.5 mm.  So the millimetre is followed
and the degree figure is corrected: 1.5 mm is 7.85 degrees of arc here.

**Latitude is a lever, not a fixed input, and that is what the last run of this
brief got wrong.**  The Sol piece leans its north pole toward the lens, so both
of its cameras look DOWN on the northern hemisphere: at the state-sheet frame
the sub-latitude is +51.5, and at a facing floor of +0.30 nothing south of
about -21 can reach the camera at ANY longitude whatever.  An earlier run put
five of its eight streaks in the south, passed its own centre-dot test, and was
still rejected because on the Sol piece everything had been crowded onto the
lower limb; it then spent all four review rounds moving longitudes and could
not fix it, because longitude is not the free variable there.  So the
latitudes below were solved together with the longitudes, against all four
cameras at once, with the spot's own facing in the objective rather than
checked afterwards.  `measure/neptune-facing.md` is that measurement.

The reference's southern preference gives way to it, and says so: six of the
eight streaks are north of -21 where all four cameras reach them, and the two
deepest -- `s1` at -50 and `s2` at -37 -- are named here and in the facing
report as Anti-Sol-only features.  A streak nobody can see is not a southern
streak, it is an absent one.

**The spot is an oval with a companion.**  It was two overlapping `blob`
circles at -22 and -20 and read as a smudge; the reference shows a clean oval
about twice as wide as it is tall.  Neptune's Great Dark Spot was about
13000 by 6600 km on a planet 49244 km across, so one degree of arc is 429.7 km
and the spot is 30.3 by 15.4 degrees -- taken here as 28 by 14, which is the
exact 2:1 the brief asks for and within 8 per cent of the measured object.  Its
latitude, -22, is the real one.  Just off its equator-facing edge sits the
small bright cloud that trails it on the real planet, and that is what stops
the spot reading as a smudge: `white`, clearly smaller than the spot, and
clearly separate from it across a gap measured against the nozzle rather than
eyeballed.

Nothing else is on this globe.  `NOT_DRAWN` below carries what was considered
and refused, and why.
"""

from __future__ import annotations

import math

import params as P

#: The globe these features are drawn for, and what one degree of it is worth.
GLOBE_D = P.globe_diameter("neptune")                 # 21.89 mm
MM_PER_DEG = math.radians(1.0) * (GLOBE_D / 2.0)      # 0.1910 mm
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


def _anticlockwise(points):
    """The same ring, ordered counter-clockwise seen from outside the globe.

    Measured rather than reasoned about.  The ring's own axis is the mean of
    its vertices -- the same axis `features/patches._ring_axis` takes -- and
    the sign of the circulation about that axis decides.  Every other ring
    source in this set (`parts/atlas.py`, `parts/jupiter_atlas.py`) states the
    order as a convention its author walked by hand; a streak is walked by a
    parametrisation instead, so the order is checked here rather than asserted.
    """
    axis = _normalise(_combine(*[(1.0, point) for point in points]))
    turn = 0.0
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        turn += _dot(_cross(point, nxt), axis)
    return points if turn >= 0.0 else list(reversed(points))


# ----------------------------------------------------------- one streak ---
#: How long a sampled edge is allowed to be along a streak's two long sides,
#: and how many segments its rounded ends are cut into.  Both are set against
#: the 0.50 mm least ring edge this set holds to everywhere -- the margin
#: `parts/mercury_atlas.py` set, a quarter of a nozzle over the 0.40 mm the
#: printer can actually lay down.
#:
#: The sides are sampled by LENGTH rather than by a fixed count, because the
#: streaks differ in length by a factor of three and a fixed count would leave
#: the shortest one with edges under the margin: at twenty samples the 5.7 mm
#: streak came out with 0.28 mm edges.  0.80 mm per edge is comfortably over
#: the margin and still puts at least seven samples on the shortest side.
#:
#: Four segments per end, not five.  A semicircle of radius w/2 cut into n
#: segments has chords of w sin(90/n) degrees, so five segments give 0.31 w --
#: 0.42 mm on the narrowest streak here, over the nozzle but under the set's
#: own margin -- and four give 0.38 w, which is 0.52 mm.  Finer is not better:
#: the end is 1.4 mm across and the argument for rounding it is that a square
#: cut reads as a broken band, which four segments already answer.
#: `measure/neptune-atlas-resolution.md` measures every edge of every ring
#: rather than trusting these two numbers.
SIDE_EDGE_MM = 0.60
CAP_SAMPLES = 4

#: How wide a streak is at its ends, as a fraction of its width at the middle,
#: and the power the taper falls off with.
#:
#: The brief allows a rounded OR a tapered end, and the first build of this
#: correction took the rounded one: every streak was a stadium, one width from
#: end to end.  Rendered at the per-world frames the eight of them read as a
#: set of parallel hatching strokes rather than as cloud -- constant width is
#: what a ruled line has, and `ref/neptune-sol.png`'s wisps are plainly
#: thickest in the middle and thin where they run out.  So the streaks taper,
#: and the rounded end is kept as well: the half-disc that closes each one is
#: simply drawn at the tapered width.
#:
#: 0.40 rather than a point, and that number is the nozzle rather than taste.
#: The narrowest streak in the family is 1.35 mm, so a 0.40 taper leaves its
#: ends 0.54 mm -- over the 0.40 mm nozzle with a third of a nozzle to spare --
#: while a taper to nothing would run the colour boundary below anything the
#: printer can lay down for the last few millimetres of every streak.
#: `measure/neptune-atlas-resolution.md` measures the end width of every one.
#:
#: The profile is  END + (1 - END) (1 - t^2)^POWER  with t the fraction of the
#: way from the middle to the end, so the width is flat across the middle
#: third and falls away over the outer third: a wisp, not a wedge.
TAPER_END = 0.40
TAPER_POWER = 1.0

def _taper(fraction: float, skew: float, end: float) -> float:
    """Width at `fraction` of the way from the streak's middle to its end.

    `fraction` runs -1 at the western end to +1 at the eastern one, `skew` is
    where along that the streak is at its widest, and `end` is the fraction of
    the full width it keeps at both ends.

    Skewed rather than symmetric, and that is the second thing an independent
    reader took off the first build of these eight.  A symmetric taper is a
    leaf: widest exactly in the middle, mirror-imaged about it, and eight of
    them read as a set of cut-out lozenges.  A cloud that is being sheared by a
    zonal wind is not symmetric -- it is blunt where it is being fed and drawn
    out where it is running away -- so each streak here is at its widest a
    fifth to a third of the way along, and which end that is alternates.
    """
    if fraction >= skew:
        value = (fraction - skew) / (1.0 - skew)
    else:
        value = (fraction - skew) / (1.0 + skew)
    return end + (1.0 - end) * (1.0 - value * value) ** TAPER_POWER


def _bend(fraction: float, amplitude: float) -> float:
    """How far the centreline bows off its own parallel, in degrees.

    One smooth hump, zero at both ends, `amplitude` at the middle -- so the
    streak is a shallow bow rather than a ruled line, and the two ends stay on
    the parallel the streak is declared at.

    This is the third thing the reader took off the first build: "hard-edged
    slashes ... roughly parallel", read off eight straight constant-width
    lozenges all lying along their own parallels.  A degree or two of bow is
    about a fifth of a millimetre of arc at the middle of a streak -- far too
    little to move where the streak is, and enough that no two of them are the
    same line.
    """
    return amplitude * math.sin(math.pi * 0.5 * (fraction + 1.0))


def streak_arc_len(lat_deg: float, lon_extent_deg: float) -> float:
    """Degrees of great-circle ARC for a streak spanning that much longitude.

    A degree of longitude is a degree of arc only on the equator; at latitude
    L it is cos L of one.  The table above is written in longitude because
    that is how the brief specifies a streak's length and how a reader reads
    one off a globe, and every measurement is taken in arc.
    """
    return lon_extent_deg * math.cos(math.radians(lat_deg))


def _spin(point, axis, angle_deg: float):
    """`point` turned about `axis` by `angle_deg`, by Rodrigues' formula."""
    angle = math.radians(angle_deg)
    cross = _cross(axis, point)
    along = _dot(axis, point)
    return _combine((math.cos(angle), point),
                    (math.sin(angle), cross),
                    (along * (1.0 - math.cos(angle)), axis))


def streak_ring(lat_deg: float, lon_deg: float, lon_extent_deg: float,
                tilt_deg: float, width_deg: float, bend_deg: float = 0.0,
                skew: float = 0.0, end: float = TAPER_END
                ) -> list[tuple[float, float]]:
    """One cloud streak as a closed (lon, lat) ring with rounded ends.

    The centreline is a segment of the PARALLEL at `lat_deg`, `lon_extent_deg`
    of longitude long and centred on `lon_deg`, and the ring is everything
    within a TAPERED half-width of it: widest at `skew` along its length,
    falling to `end` of that at both ends, and closed there by a half-disc of
    the narrowed radius.  The centreline itself bows `bend_deg` off the
    parallel at its middle and returns to it at both ends.  A wisp rather than
    a ruled line.  The whole ring is then turned `tilt_deg` about its own centre,
    which tips the eastern end north for a positive tilt and leaves the shape
    itself untouched, because a rotation about a point of the sphere is an
    isometry of the sphere.

    A parallel rather than a great circle, and that is measured rather than
    stylistic.  A great-circle arc through latitude -52 running east rises to
    -45 within 26 degrees of arc -- it arches seven degrees toward the equator
    at each end -- so a streak drawn on one is not at the latitude it is
    declared at, and two streaks fifteen degrees apart in latitude collided in
    `measure/neptune-atlas-resolution.md` at 0.01 mm.  Cloud bands follow
    latitude in any case: that is what a zonal wind is.

    The width is exact.  The angular distance from a point at latitude
    `lat - w/2` to the parallel at `lat` is measured along the meridian, which
    crosses the parallel square, and is exactly `w/2` at every longitude.  So
    the two long sides are `w` apart everywhere, however far north the streak
    sits -- which an offset in degrees of LONGITUDE would not be, because a
    degree of longitude shortens with the cosine of the latitude and the
    streak would pinch toward the pole.
    """
    half_width = width_deg / 2.0
    half_lon = lon_extent_deg / 2.0
    centre = _unit(lon_deg, lat_deg)
    side_samples = max(5, int(math.ceil(
        streak_arc_len(lat_deg, lon_extent_deg) * MM_PER_DEG / SIDE_EDGE_MM)))

    points = []

    def side(sign: float, eastward: bool):
        """One long side, `sign` x the tapered half-width off the centreline."""
        for step in range(side_samples + 1):
            fraction = step / side_samples if eastward else 1.0 - step / side_samples
            along = 2.0 * fraction - 1.0
            points.append(_unit(
                lon_deg - half_lon + 2.0 * half_lon * fraction,
                lat_deg + _bend(along, bend_deg)
                + sign * half_width * _taper(along, skew, end)))

    def cap(lon_end: float, outward: float, start: float):
        """Half a circle of radius `half_width` about one end of the centreline.

        Swept from the `start` side of the centreline round through the outward
        tip to the other side, so the end is a half-disc rather than a square
        cut -- a square end is the one thing that makes a short band read as a
        broken band rather than as a cloud.  The two extreme samples are the
        sides' own last points and are left to them, which keeps the four
        pieces of the ring one closed curve with no repeated vertex.
        """
        tip_centre = _unit(lon_end, lat_deg)
        east = _normalise(_cross((0.0, 0.0, 1.0), tip_centre))
        up = _cross(tip_centre, east)
        reach = math.radians(half_width * end)
        for step in range(1, CAP_SAMPLES):
            phi = math.pi * step / CAP_SAMPLES
            points.append(_combine(
                (math.cos(reach), tip_centre),
                (math.sin(reach) * math.cos(phi) * start, up),
                (math.sin(reach) * math.sin(phi) * outward, east)))

    side(-1.0, True)                              # west to east, southern side
    cap(lon_deg + half_lon, 1.0, -1.0)            # round the eastern end
    side(1.0, False)                              # east to west, northern side
    cap(lon_deg - half_lon, -1.0, 1.0)            # round the western end

    ring = _anticlockwise([_spin(point, centre, tilt_deg) for point in points])
    return [(round(lon, 4), round(lat, 4))
            for lon, lat in (_lon_lat(point) for point in ring)]


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


# --------------------------------------------------------- the streaks ---
def _width_deg(width_mm: float) -> float:
    return width_mm / MM_PER_DEG


#: (key, latitude, longitude, length in degrees of LONGITUDE, tilt, width mm).
#:
#: Read the six columns rather than the names.  No two lengths are equal, no
#: two latitudes, no two longitudes and no two widths; six of the eight carry a
#: tilt of two to six degrees against the parallel and two run level, so the
#: family does not read as a set of level rules.  The lengths span 28 to 86
#: degrees of longitude -- the brief's own range -- and the longitudes span 70
#: degrees, so they do not stack into a column.
#:
#: The latitudes and the longitudes were solved TOGETHER against the four
#: cameras, with the spot in the objective, and that is the whole difference
#: between this table and the one the last run of this brief was rejected for.
#: `measure/neptune-facing.md` carries the dot products.  The shape of the
#: answer:
#:
#:   * `s3` to `s8`, six of the eight, sit north of -21, which is the deepest
#:     latitude the Sol state-sheet camera can reach at a facing floor of
#:     +0.30.  All four cameras see all six.
#:   * `s1` at -50 and `s2` at -37 are the two southern streaks and they are
#:     Anti-Sol-only features.  They are named as such here, in the facing
#:     report and in the product's limitations.  They are kept because the
#:     reference's clouds are southern-weighted and because the Anti-Sol piece,
#:     which leans its north pole away from the lens, shows them well; they are
#:     not moved north because two deep southern wisps are what stops the
#:     northern six reading as a ladder.
#:
#: The widths vary from 1.35 to 1.65 mm about the owner's 1.50, the way the
#: earlier attempt varied 2.6 to 3.6 degrees, and the family stays near 1.5 mm
#: rather than near the nozzle.
STREAKS = (
    # key    lat      lon   extent  tilt  width  bend  skew   end
    ("s1", -52.0,  -14.5,  90.0,   4.0, 1.40,  1.6, -0.24, 0.38),
    ("s2", -37.0,  -77.6,  76.0, -11.0, 1.55, -1.1,  0.30, 0.46),
    ("s3", -10.0, -102.5,  46.0,   7.0, 1.35, -1.6,  0.22, 0.34),
    ("s4",   4.0, -108.4,  60.0,  -3.0, 1.60,  1.4, -0.30, 0.42),
    ("s5",  17.0,  -22.2,  54.0,  12.0, 1.45, -1.2, -0.18, 0.50),
    ("s6",  28.0,   18.5,  72.0,  -6.0, 1.50,  2.0,  0.26, 0.36),
    ("s7",  38.0,  -44.2,  58.0,   3.0, 1.65, -1.5,  0.32, 0.44),
    ("s8",  47.0, -114.9,  84.0,  -9.0, 1.50,  1.7, -0.26, 0.40),
)

#: Which of the eight the Sol piece's own two cameras cannot reach whatever
#: their longitude, stated here so a reader of the rendered Sol piece finds the
#: reason before reporting a missing streak.
ANTI_SOL_ONLY = ("s1", "s2")


STREAK_RINGS = {
    key: streak_ring(lat, lon, extent, tilt, _width_deg(width), bend, skew, end)
    for key, lat, lon, extent, tilt, width, bend, skew, end in STREAKS
}


# ------------------------------------------- the spot and its companion ---
#: 13000 by 6600 km at 429.7 km per degree of arc is 30.3 by 15.4 degrees,
#: taken as 28 by 14: the exact 2:1 the brief asks for, within 8 per cent of
#: the measured object.  Semi-axes, in degrees of great-circle arc.
SPOT_LAT = -22.0
SPOT_LON = -65.2
SPOT_SEMI_ARC_LON = 14.0
SPOT_SEMI_ARC_LAT = 7.0

#: The bright companion, on the spot's equator-facing -- northern -- side.
#:
#: It is a STREAK rather than an oval, and it HUGS the spot's own rim.  Both
#: are repairs rather than first choices, and both came off the same
#: independent reader, three reads running.  Drawn as a small oval beside the
#: spot it was read as "a stray droplet, like a piece that broke off the main
#: ellipse".  Redrawn as a long thin wisp carried seven degrees east it was
#: read as "a stray fragment ... no visual relationship to it".  Redrawn
#: compact and centred over the spot it was still "a small pale lozenge
#: floating above the grey blob with no shared edge ... no sense that one is a
#: part of the other".  The companion exists to stop the spot reading as a
#: smudge, so it has to read as BELONGING to the spot, and three attempts say
#: proximity alone will not do it.
#:
#: So its lower edge is now drawn PARALLEL TO THE SPOT'S UPPER EDGE at a
#: constant clearance, which is the one relationship a reader cannot miss.
#: The spot is an ellipse 14 by 7 degrees of arc, so its upper edge falls away
#: from +7.0 at its own meridian to +5.94 at the companion's ends, a sagitta of
#: 1.06 degrees; the companion carries exactly that as its bow, so the strip of
#: bare globe between the two is the same width all the way along instead of
#: pinching in the middle and opening at the ends.
#:
#: Everything else about it stays what the correction asks for: `white`, one of
#: the nine bodies of the `streaks` marking, 15 degrees of longitude long --
#: about half the spot's own length -- and 1.45 mm wide, inside the streak
#: family's own 1.35 to 1.65 mm so it prints and reads like the other white on
#: this globe.  No tilt, because a tilt would break the one symmetry that makes
#: it read as the spot's own.
#:
#: The clearance is the number that matters and it is set against the nozzle:
#: 3.14 degrees of arc is 0.60 mm, half a nozzle clear of the 0.40 mm the
#: printer can lay down, so the two markings are clearly separate and stay
#: separate.  The correction's instruction if that gap were short is to move
#: the companion rather than shrink it, and that is the rule its latitude is
#: set by -- its size was chosen first and the clearance decided where it sits.
#: `measure/neptune-atlas-resolution.md` measures the gap on the two exact
#: rings rather than taking it from the numbers here.
COMPANION_GAP_DEG = 3.14
COMPANION_WIDTH_MM = 1.45
COMPANION_EXTENT_DEG = 15.0
COMPANION_TILT_DEG = 0.0
COMPANION_BEND_DEG = 1.06
COMPANION_LAT = (SPOT_LAT + SPOT_SEMI_ARC_LAT + COMPANION_GAP_DEG
                 + 0.5 * COMPANION_WIDTH_MM / MM_PER_DEG - COMPANION_BEND_DEG)
COMPANION_LON = SPOT_LON + 2.0

#: The spot's vertex count.  40 rather than the 22 the first build used, and
#: that is a repair: an independent reader of the 22-vertex oval reported
#: "straight facets and corners on its lower left ... a low-polygon shape
#: rather than an oval", which is precisely what this correction replaced two
#: overlapping circles to avoid.  An ellipse walked at even bearings puts its
#: samples furthest apart at the two pointed ends, so the count has to be set
#: by the ends rather than by the average: at 22 the end chord fell 0.055 mm
#: inside the true ellipse and at 40 it falls 0.017 mm inside, a twelfth of a
#: nozzle.  The shortest edge drops to about 0.21 mm, which is a facet of a
#: curve rather than the width of anything -- the spot's own narrowest neck
#: stays its 2.67 mm minor axis, and `measure/neptune-atlas-resolution.md`
#: measures that rather than inferring it.
SPOT_VERTICES = 40

SPOT_RING = oval_ring(SPOT_LAT, SPOT_LON, SPOT_SEMI_ARC_LON,
                      SPOT_SEMI_ARC_LAT, SPOT_VERTICES)
COMPANION_RING = streak_ring(COMPANION_LAT, COMPANION_LON,
                             COMPANION_EXTENT_DEG, COMPANION_TILT_DEG,
                             _width_deg(COMPANION_WIDTH_MM),
                             bend_deg=COMPANION_BEND_DEG, skew=0.0, end=0.45)


# ----------------------------------------------- what markings ask for ---
def streak_specs():
    """The region specs `parts/markings.py` gives the `streaks` marking.

    One `outline` spec carrying all eight streaks and the companion, so the
    whole white marking is one region with one key and one filament, exactly
    as the three `band` regions it replaces were.  The companion belongs here
    rather than beside the spot because it is white: the marking key is the
    filament, not the feature.
    """
    return [("outline", [STREAK_RINGS[key] for key, *_rest in STREAKS]
             + [COMPANION_RING])]


def spot_specs():
    """The region specs `parts/markings.py` gives the `spot` marking."""
    return [("outline", [SPOT_RING])]


# ------------------------------------------------------------ the record --
#: name -> ring, for the resolution report and the facing report.
RINGS = dict(STREAK_RINGS)
RINGS["companion"] = COMPANION_RING
RINGS["spot"] = SPOT_RING

NOT_DRAWN = (
    "Neptune's globe is Ø%.2f mm, so one degree of arc is %.4f mm and a "
    "%.1f mm nozzle is %.2f degrees of it. Considered and refused: a SECOND "
    "DARK SPOT -- the reference shows one and the brief forbids a second; "
    "POLAR BRIGHTENING -- the reference shows none, and a bright cap on this "
    "globe would repeat Saturn's northern cap on the world two ranks below it; "
    "RING ARCS -- Neptune has rings, the reference does not show them, this "
    "set does not draw them, and a ring on rank 5 would collide with Saturn's "
    "role at rank 7 in the size ladder, where the ring IS the rank; a FAINT "
    "DARKER CENTRE inside the dark spot, which the reference shows and which "
    "would need a fourth filament on a globe the brief holds to three; and the "
    "reference's own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm "
    "here, under one nozzle width, and would print as noise. The set's "
    "material rules forbid deliberate grit."
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG)
)
