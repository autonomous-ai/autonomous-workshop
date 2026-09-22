"""Mercury's smooth plains and the Caloris basin, as closed lon/lat rings.

The third of the three worlds in this set whose surface is drawn from outlines
rather than from a union of round patches.  Earth's coastlines are in
`parts/atlas.py`, Mars's classical albedo map in `parts/mars_atlas.py`, and
Mercury's are here.  The other five worlds keep their blobs and bands, because
a cloud pattern, a band system and a storm genuinely are round.

Mercury is the softest of the three and the smallest globe in the set at
Ø13.78 mm, where one degree of arc is 0.120 mm and a 0.4 mm nozzle is 3.33
degrees of it.  Two consequences run through everything below.

The first is that Mercury's albedo boundaries are genuinely soft and genuinely
unnamed, so there is no silhouette anybody can check a ring against the way
Africa's coast or Syrtis Major's triangle can be checked.  The rings are
therefore *generated* from a documented deterministic formula rather than
carried as survey data: a mean angular radius about the patch's own centre,
modulated by three low harmonics.  Harmonics one to three only -- a fourth or
fifth would be sampled three or four times per period at these vertex counts
and would come out as a jagged edge rather than as a lobe.  What the formula
is asked to produce is what the reference shows: smooth, lobed, unequal
regions, several of which run together into one larger smooth plain.

The second is that a circle is the one shape a plain must not be.  A union of
discs is what made the previous Mercury read as a beach ball, and a true
circle at Caloris's size reads as a manufacturing mark rather than as a crater.
Every ring here is irregular for that reason, Caloris's two included.

Craters are deliberately absent, and that is not a matter of taste.  See
`CRATERS_NOT_DRAWN`.
"""

from __future__ import annotations

import math

import params as P

#: The globe these rings are drawn for, and what one degree of it is worth.
GLOBE_D = P.globe_diameter("mercury")                 # 13.78 mm
MM_PER_DEG = math.radians(1.0) * (GLOBE_D / 2.0)      # 0.1203 mm
NOZZLE_DEG = P.NOZZLE_MM / MM_PER_DEG                 # 3.33 degrees of arc


# ------------------------------------------------------------ ring maths ---
def _unit(lon_deg: float, lat_deg: float) -> tuple[float, float, float]:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def _lon_lat(vector) -> tuple[float, float]:
    x, y, z = vector
    return (math.degrees(math.atan2(y, x)),
            math.degrees(math.asin(max(-1.0, min(1.0, z)))))


def lobed_ring(lat_deg: float, lon_deg: float, radius_deg: float,
               lobes, count: int, unwrap_near: float | None = None):
    """A closed ring around one centre, walked at `count` even bearings.

    `lobes` is a list of `(harmonic, amplitude, phase_deg)`.  The angular
    radius at bearing theta -- measured from north, positive toward east -- is

        r(theta) = radius_deg * (1 + sum a_k cos(k theta - phase_k))

    so harmonic one makes the region an egg pointing one way, harmonic two an
    ellipse, harmonic three a three-lobed plain.  Returned counter-clockwise
    in (longitude, latitude) degrees, the same convention `parts/atlas.py`
    uses.

    `unwrap_near` keeps a ring that straddles the +/-180 seam continuous in
    longitude by reporting every vertex within half a turn of that value.
    Nothing in the construction cares -- `features/patches.py` turns the pair
    straight back into a unit vector -- but a ring listed as 190, 200, -170 is
    unreadable, and this is what a reader has to read.
    """
    centre = _unit(lon_deg, lat_deg)
    north = (0.0, 0.0, 1.0)
    east = _normalise(_cross(north, centre))
    up = _cross(centre, east)
    ring = []
    for index in range(count):
        # Counter-clockwise seen from outside the globe is decreasing bearing.
        theta = -2.0 * math.pi * index / count
        scale = 1.0 + sum(
            amplitude * math.cos(harmonic * theta - math.radians(phase))
            for harmonic, amplitude, phase in lobes
        )
        reach = math.radians(radius_deg * scale)
        point = tuple(
            math.cos(reach) * centre[axis]
            + math.sin(reach) * (math.cos(theta) * up[axis]
                                 + math.sin(theta) * east[axis])
            for axis in range(3)
        )
        lon, lat = _lon_lat(point)
        if unwrap_near is not None:
            while lon - unwrap_near > 180.0:
                lon -= 360.0
            while unwrap_near - lon > 180.0:
                lon += 360.0
        ring.append((round(lon, 3), round(lat, 3)))
    return ring


def _cross(one, other):
    return (one[1] * other[2] - one[2] * other[1],
            one[2] * other[0] - one[0] * other[2],
            one[0] * other[1] - one[1] * other[0])


def _normalise(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


#: The least a ring edge may measure on this globe.  The nozzle is 0.40 mm and
#: a colour boundary cannot be laid down narrower than that, so an edge shorter
#: than it is a vertex the printer cannot resolve.  0.50 leaves a quarter of a
#: nozzle of margin.
MIN_EDGE_MM = 0.50

#: The most vertices any ring here gets.  Past this the edges fall under
#: MIN_EDGE_MM on every ring in the atlas anyway.
MAX_VERTICES = 24


def vertex_count(radius_deg: float, lobes) -> int:
    """The most vertices this ring can carry and still clear MIN_EDGE_MM.

    A lobed ring is shortest where its radius is least, so the count is
    chosen against the ring's own minimum radius rather than its mean: a
    strongly lobed plain gets fewer, larger steps, and a nearly round one gets
    more.  Deterministic, and reported ring by ring in
    `measure/mercury-atlas-resolution.md`.
    """
    least = radius_deg * (1.0 - sum(amplitude for _k, amplitude, _p in lobes))
    for count in range(MAX_VERTICES, 5, -1):
        edge = 2.0 * math.pi * least * MM_PER_DEG / count
        if edge >= MIN_EDGE_MM:
            return count
    return 6


# --------------------------------------------------------- smooth plains ---
#: The seven albedo patches, at the exact centres the round-patch build used.
#: Only their outline changed: (name, latitude, longitude, mean angular
#: radius, lobes); the vertex count is derived from the ring's own least
#: radius.  The radii are unequal on purpose -- the reference's
#: plains are unequal -- and each carries its own harmonic-one direction, so
#: no two of them are the same egg turned round.
#:
#: The globe is cut off where it sinks into its disc, and the seat cone springs
#: at latitude -42, so everything south of -42 is buried and invisible.  A
#: boundary landing in the 3.33 degrees just north of that line would leave a
#: strip of bare gray too thin to print, so every southern lobe here is held
#: clear of it.  `measure/mercury-atlas-resolution.md` measures that.
PLAINS_SPECS = (
    ("plain_north_west", 18.0, 24.0, 22.0,
     ((1, 0.14, 300.0), (2, 0.14, 40.0), (3, 0.08, 200.0))),
    ("plain_equatorial", 6.0, 48.0, 20.0,
     ((1, 0.16, 45.0), (2, 0.13, 190.0), (3, 0.07, 90.0))),
    ("plain_south_lead", -22.0, 118.0, 20.0,
     ((1, 0.26, 0.0), (2, 0.12, 110.0), (3, 0.07, 300.0))),
    ("plain_south_mid", -10.0, 138.0, 16.0,
     ((1, 0.20, 20.0), (2, 0.14, 260.0), (3, 0.07, 150.0))),
    ("plain_high_north", 38.0, 205.0, 21.0,
     ((1, 0.15, 150.0), (2, 0.13, 70.0), (3, 0.07, 320.0))),
    ("plain_far_side", -6.0, 255.0, 18.0,
     ((1, 0.22, 350.0), (2, 0.12, 40.0), (3, 0.08, 130.0))),
    ("plain_trailing", 2.0, 162.0, 14.0,
     ((1, 0.18, 210.0), (2, 0.15, 100.0), (3, 0.09, 15.0))),
)

PLAINS_RINGS = [
    lobed_ring(lat, lon, radius, lobes, vertex_count(radius, lobes),
               unwrap_near=lon)
    for _name, lat, lon, radius, lobes in PLAINS_SPECS
]

#: Which of them the boolean is expected to fuse into one larger plain.  The
#: reference shows the smooth plains running together rather than sitting apart
#: as separate discs; these three and this pair are where that happens, and
#: `measure/mercury-surface.md` measures whether the kernel agreed.
PLAINS_EXPECTED_GROUPS = (
    ("plain_south_lead", "plain_south_mid", "plain_trailing"),
    ("plain_north_west", "plain_equatorial"),
)


# ------------------------------------------------------- the Caloris basin --
#: Caloris Planitia is about 1550 km across on a planet 4879 km in diameter.
#: 1550 / 4879 is 0.3177 of the diameter, which is 2 * asin(0.3177) = 37.0
#: degrees of arc -- an angular radius of 18.5, rounded to the 18 the Wish
#: carries, and 2 * 18 * 0.1203 = 4.33 mm across on this globe.
#:
#: It is built as two concentric rings rather than as a circle union: a bright
#: interior floor, and the rim annulus left when that floor is subtracted out
#: of the outer ring.  That is what makes it read as a basin with a raised edge
#: rather than as a painted dot, and it is what the reference shows -- a large
#: bright circular plain with a distinct brighter rim around it.
CALORIS_LAT = 30.0

#: Longitude is free: Mercury turns on no meridian this set fixes, and the Wish
#: asks for whatever longitude puts the basin on the camera-facing hemisphere.
#: -50 is the measured answer.  The two photographed frames look along azimuth
#: -55 (the hero) and -45 (the state sheet), and a feature at latitude +30
#: faces a frame most squarely when its longitude equals that azimuth; -50 is
#: the midpoint, and lands 0.99 against both view axes on both armies.
#: `measure/mercury-facing.md` is that measurement, and the comment in
#: `parts/markings.py` carries the numbers.
CALORIS_LON = -50.0

CALORIS_RIM_RADIUS = 18.0
CALORIS_FLOOR_RADIUS = 10.5

#: Both outlines are scalloped rather than circular.  A true circle at 4.3 mm
#: reads as a manufacturing mark -- a drilled hole or a moulding pip -- and the
#: reference's basin edge is visibly scalloped.  The amplitudes are small on
#: purpose: they have to break the circle without letting the rim annulus
#: narrow below the 0.4 mm nozzle anywhere round the ring, and the narrowest
#: annulus is measured rather than assumed.
CALORIS_RIM_LOBES = ((2, 0.055, 30.0), (3, 0.050, 150.0), (4, 0.030, 260.0))
CALORIS_FLOOR_LOBES = ((2, 0.070, 90.0), (3, 0.055, 20.0), (4, 0.030, 200.0))

CALORIS_RIM = lobed_ring(CALORIS_LAT, CALORIS_LON, CALORIS_RIM_RADIUS,
                         CALORIS_RIM_LOBES,
                         vertex_count(CALORIS_RIM_RADIUS, CALORIS_RIM_LOBES))
CALORIS_FLOOR = lobed_ring(CALORIS_LAT, CALORIS_LON, CALORIS_FLOOR_RADIUS,
                           CALORIS_FLOOR_LOBES,
                           vertex_count(CALORIS_FLOOR_RADIUS,
                                        CALORIS_FLOOR_LOBES))


# ------------------------------------------------------------- the record --
#: name -> ring, for the resolution report and for naming a ring in a message.
RINGS = {spec[0]: ring for spec, ring in zip(PLAINS_SPECS, PLAINS_RINGS)}
RINGS["caloris_rim"] = CALORIS_RIM
RINGS["caloris_floor"] = CALORIS_FLOOR

PLAIN_NAMES = [spec[0] for spec in PLAINS_SPECS]

#: Why there is no crater field, stated here so a later reader finds it before
#: reopening it.  This is the note the round-patch build already carried, with
#: the number added.
CRATERS_NOT_DRAWN = (
    "Mercury is the smallest globe in the set at Ø%.2f mm, so one degree "
    "of arc is %.3f mm and a %.1f mm nozzle is %.2f degrees of it. The "
    "reference shows craters everywhere, and the largest of them outside "
    "Caloris subtend three to six degrees -- one or two nozzle widths, with "
    "no room for a rim and a floor inside that. A crater drawn at this "
    "radius prints as a pit the width of a single extrusion and reads as a "
    "print defect rather than as a crater, and the set's material rules "
    "forbid deliberate grit. Caloris is the exception and is included "
    "precisely because it is the one impact feature large enough to survive: "
    "at 36 degrees of arc it is eleven nozzle widths across."
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG)
)

#: ring name -> what this build coarsened and by how much.  Empty means every
#: ring above is carried exactly as the formula draws it.
#: `measure/mercury-atlas-resolution.md` is the measurement this is read from.
SIMPLIFIED: dict[str, str] = {
    "plain_south_lead": (
        "mean angular radius 20.0 rather than the 22.0 the round patch used, "
        "and the strongest harmonic-one bias of the seven at 0.24 pointing "
        "north.  Drawn at 22 and evenly, its southern boundary reached "
        "latitude -44, which is past the -42 parallel where the seat cone "
        "springs and the visible sphere ends: the plain would have run out of "
        "globe, and anywhere it stopped just short would have left a strip of "
        "bare gray under the 0.4 mm nozzle.  Pulled north, the boundary "
        "stands at -37.6 and leaves 4.4 degrees, 0.53 mm, of visible gray "
        "between the plain and the seat.  The centre did not move."
    ),
}
