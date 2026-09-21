"""Jupiter's belt system, its bright zones and the Great Red Spot.

Jupiter used to wear six `cocoa_brown` latitude bands, every one of them
exactly 12 degrees wide, at -56/-44, -36/-24, -16/-4, 4/16, 24/36 and 44/56.
Equal width, equal spacing, perfectly symmetric about the equator.  That is a
beach ball.  Nothing in the sky is regular like that, and `ref/jupiter-sol.png`
is not: its bands differ in width by a factor of three, the belts north and
south of the equator are visibly unequal, the pattern does not repeat, and the
broad bright equatorial zone is the widest feature on the planet.  Regularity
is the single thing that tells a viewer they are looking at a manufactured
object rather than at a planet.

Three things are drawn here, and the arithmetic that decides all three is the
same: Jupiter's globe is the largest in the set at 26.97 mm, so one degree of
arc is 0.2354 mm and the 0.4 mm nozzle is 1.70 degrees of it.  This is the most
forgiving world in the chain, and it is still the number every feature below is
checked against in `measure/jupiter-atlas-resolution.md`.

**The belts are the real ones.**  Six of them, as before, so the print cost
does not change -- but at the latitudes Jupiter's belts actually occupy, which
are neither evenly spaced nor symmetric.  The South Equatorial Belt is the
widest at 13 degrees and the North North Temperate the narrowest at 5.

**The zones are a third tone.**  The reference has a base colour, darker belts
*and* bright cream zones between them; the previous build had orange and cocoa
only, so the bright zones were bare globe and the piece lost the alternating
rhythm that makes Jupiter legible.  Five zones are drawn in `beige`, measured
against `orange` and `cocoa_brown` in `measure/jupiter-tone-separation.md`.
Each zone is drawn wider than it ends up and has the belts subtracted out of
it, the way Earth's `dryland` sits inside `land`: that is what lets a zone
boundary follow a wavy belt boundary exactly instead of being typed twice.

**Two belt boundaries are outlines rather than circles of latitude.**  The
Earth run established that an exact circle of latitude reads as a machined
edge.  The two widest belts -- South Equatorial and North Equatorial -- carry a
2.5 degree wave on both boundaries, drawn as closed longitude/latitude rings in
six longitude sectors each.  The other four belts stay plain `band` regions: at
5 to 7 degrees wide a wave would eat the band.

A belt that encircles the globe is an annulus, and a radial cone through one
closed ring can never be an annulus, so a wavy belt is cut into sectors that
abut along exact radial planes and fuse back into one body.  Six sectors of 60
degrees keeps every vertex about 30 degrees from its own sector's axis, well
inside the 72 degree limit `features/patches.py` holds its outline
construction to.

**The spot is an oval, not a lozenge.**  It was three overlapping circles and
read as one.  The real spot is about 16000 by 11000 km; Jupiter is 139820 km
across, so one degree of arc is 1220 km and the spot is 13 degrees wide by 9
tall -- half again wider than it is tall, which is what the reference shows.
It is not the long thin oval of nineteenth-century drawings; the spot has been
shrinking for a century.  It gets a `cocoa_brown` collar just outside it so it
has an edge rather than floating, and the South Equatorial Belt's southern
boundary bends north around it instead of running straight past.
"""

from __future__ import annotations

import math

import params as P

#: The globe these features are drawn for, and what one degree of it is worth.
GLOBE_D = P.globe_diameter("jupiter")                 # 26.97 mm
MM_PER_DEG = math.radians(1.0) * (GLOBE_D / 2.0)      # 0.2354 mm
NOZZLE_DEG = P.NOZZLE_MM / MM_PER_DEG                 # 1.70 degrees of arc

#: Jupiter's real equatorial diameter, and the kilometres one degree of arc on
#: it is worth.  This is the arithmetic the spot's size comes from.
DIAMETER_KM = P.PLANETS["jupiter"]["d_km"]            # 139820 km
KM_PER_DEG = math.pi * DIAMETER_KM / 360.0            # 1220 km


# ------------------------------------------------------------- the belts ---
#: (key, name, southern latitude, northern latitude, how it is drawn).
#:
#: These are Jupiter's actual belts.  Read the widths rather than the names:
#: 7, 10, 13, 7, 5, 6.  No two of the pairs are mirror images and no two gaps
#: between them are equal, which is the whole point of the correction.
BELTS = (
    ("nntb", "North North Temperate Belt", 38.0, 43.0, "band"),
    ("ntb", "North Temperate Belt", 24.0, 31.0, "band"),
    ("neb", "North Equatorial Belt", 7.0, 17.0, "outline"),
    ("seb", "South Equatorial Belt", -20.0, -7.0, "outline"),
    ("stb", "South Temperate Belt", -34.0, -27.0, "band"),
    ("sstb", "South South Temperate Belt", -46.0, -40.0, "band"),
)

#: (key, name, southern latitude, northern latitude, drawn south, drawn north).
#:
#: The first pair is what the zone IS.  The second is the constant-depth
#: latitude shell actually handed to the build, which overruns into the belt on
#: either side; `parts/world.py` cuts the belts first and carries the remainder
#: forward, so every zone boundary ends up being the face the belt's own cut
#: left, and the overrun itself never appears.
#:
#: A boundary overruns only where the belt beside it MOVES.  The two wavy
#: belts swing 2.5 degrees either way and the South Equatorial Belt's southern
#: boundary bends 7.0 degrees north over the Great Red Spot, so a zone that
#: abuts one of those is drawn past every position it can reach -- otherwise a
#: thread of bare globe is left where the belt waves away from it.
#:
#: A zone that abuts one of the four plain belts is drawn to that belt's exact
#: latitude and not a fraction of a degree further, and that zero is measured
#: rather than tidy.  A `band` lens tapers to nothing at its own edge, so a
#: zone drawn past one does not get trimmed by it -- it runs UNDERNEATH the
#: belt's feather at full depth.  Drawn a whole degree past, that buried
#: `beige` cut the orange globe into three separate solids.  Drawn a quarter of
#: a degree past, the globe stayed whole but the two bodies interlocked along
#: the feather's knife edge, and `inspect interfere` could not answer the pair:
#: it reported the South Temperate Belt's entire 51.52 mm3 as a clash with the
#: South Tropical Zone on the Anti-Sol world and nothing at all on the Sol
#: world, from geometry that is a mirror of it.  At zero the zone's cone lands
#: exactly on the circle where the belt's lens meets the globe, the two bodies
#: meet on a curve rather than interlocking, and the gate is clean on both
#: armies.  The shard that the quarter-degree overrun was reached for is cured
#: by ZONE_FLOOR_CLEARANCE instead, which is where it belonged.
#:
#: No two of these five ranges may overlap either, or the two shells fuse under
#: the belt between them and what should be two bright zones comes out as one
#: body.
#:
#: The poles above +46 and below -46 are left bare.  The reference darkens
#: toward the poles rather than brightening, and bare orange is closer to that
#: than a bright zone would be.
ZONES = (
    ("ez", "Equatorial Zone", -7.0, 7.0, -11.0, 12.0),
    ("ntrz", "North Tropical Zone", 17.0, 24.0, 13.0, 24.0),
    ("strz", "South Tropical Zone", -27.0, -20.0, -27.0, -12.0),
    ("ntz", "North Temperate Zone", 31.0, 38.0, 31.0, 38.0),
    ("stz", "South Temperate Zone", -40.0, -34.0, -40.0, -34.0),
)

#: How far the zones stop SHORT of the depth every other marking on this globe
#: bottoms out at.  The belts, the spot and the collar are outline lenses and
#: their floor is the sphere at RELIEF_DEPTH below the surface; a zone drawn to
#: the same depth has the same floor, and two markings whose floors are the
#: same sphere described twice is the boolean this kernel answers wrongly
#: rather than slowly.  Measured on this build: at equal depth the split left a
#: 0.03 mm3 shard of bare globe floating six microns under the surface and the
#: orange globe came out as two solids -- and as three on the Sol world against
#: two on the Anti-Sol one, so the two armies stopped being exact mirrors.  At
#: 0.06 mm of clearance, an eighth of a layer, every body is single, the two
#: armies agree to 3e-5 mm3, and nothing is visible either way: the clearance
#: is under the globe's surface, not on it.
ZONE_FLOOR_CLEARANCE = 0.06
ZONE_DEPTH = P.RELIEF_DEPTH - ZONE_FLOOR_CLEARANCE     # 1.14 mm

#: The filament the zones print in.  `beige` #F7E6DE against the `orange`
#: #FF671F globe and the `cocoa_brown` #8E3C06 belts, measured in the canonical
#: render rather than read off the catalogue, in
#: `measure/jupiter-tone-separation.md`.  It is already in the set -- Earth's
#: dryland and Venus's highlands -- so it loads no new spool.
ZONE_COLOUR = "beige"


# --------------------------------------------------------------- the wave --
#: How far a wavy belt boundary departs from its own circle of latitude, at
#: most, in degrees.  Two or three is the brief: enough to take the lathe look
#: off the edge, not enough to read as turbulence.  Each boundary carries two
#: harmonics of longitude with different periods and phases, so no two of the
#: four boundaries move together and the pattern does not repeat round the
#: globe.
WAVE_AMPLITUDE_DEG = 2.5

#: boundary -> ((harmonic, amplitude, phase degrees), ...), summed as
#: `amplitude * sin(harmonic * longitude + phase)`.  The amplitudes of each
#: pair total WAVE_AMPLITUDE_DEG.
WAVES = {
    ("neb", "south"): ((3, 1.5, 0.0), (4, 1.0, 110.0)),
    ("neb", "north"): ((2, 1.4, 250.0), (5, 1.1, 40.0)),
    ("seb", "north"): ((3, 1.6, 200.0), (4, 0.9, 20.0)),
    ("seb", "south"): ((2, 1.5, 70.0), (3, 1.0, 310.0)),
}


def wave(key: str, edge: str, lon_deg: float) -> float:
    """The departure of one belt boundary from its own parallel, in degrees."""
    return sum(
        amplitude * math.sin(math.radians(harmonic * lon_deg + phase))
        for harmonic, amplitude, phase in WAVES[(key, edge)]
    )


# ------------------------------------------------------ the Great Red Spot --
#: Latitude is the real one.  Longitude is free -- Jupiter turns in ten hours
#: and this set fixes no meridian -- and -48 is where the existing -110 degree
#: carry put it, measured so that the spot faces the camera in both
#: photographed frames on both armies.  That measurement is preserved rather
#: than repeated from scratch; `measure/jupiter-facing.md` re-measures it
#: against the oval this revision draws.
SPOT_LAT = -22.0
SPOT_LON = -48.0
SPOT_CARRY_DEG = -110.0

#: 16000 by 11000 km at 1220 km per degree of arc: 13.1 by 9.0, taken as 13 by
#: 9.  Semi-axes, in degrees of arc on the sphere -- not degrees of longitude,
#: which at latitude -22 are 7.8 per cent shorter.
SPOT_SEMI_ARC_LON = 6.5
SPOT_SEMI_ARC_LAT = 4.5

#: The collar: a second ring outside the red one, so the spot has an edge
#: rather than floating.  2.00 degrees of arc is 0.47 mm, which clears the 0.4
#: mm nozzle; a collar the 1.2 degrees that would keep it clear of the South
#: Temperate Belt is 0.28 mm and could not be printed as a colour boundary.
#: Where the collar reaches past latitude -27 it is cut back by that belt,
#: which is `cocoa_brown` too, so the two simply meet -- measured, over 12
#: degrees of longitude and 1.5 of latitude, in
#: `measure/jupiter-atlas-resolution.md`.
COLLAR_WIDTH_DEG = 2.0
COLLAR_SEMI_ARC_LON = SPOT_SEMI_ARC_LON + COLLAR_WIDTH_DEG
COLLAR_SEMI_ARC_LAT = SPOT_SEMI_ARC_LAT + COLLAR_WIDTH_DEG

#: The hollow the spot bites out of the South Equatorial Belt.  At the spot's
#: own meridian the belt's southern boundary stands at -20 + 7.0 = -13.0
#: instead of -20, and it returns to its wave within about 25 degrees of
#: longitude either side.  That is the detail that makes the spot look like it
#: belongs to the weather rather than like a sticker: the belt bends around it.
#:
#: The wave is faded out in proportion as the hollow comes in, so the two do
#: not add up and drive the boundary somewhere neither of them intended.
HOLLOW_DEPTH_DEG = 7.0
HOLLOW_SIGMA_DEG = 11.0


def _hollow(lon_deg: float) -> float:
    """0 far from the spot, 1 at its own meridian."""
    offset = ((lon_deg - SPOT_LON + 180.0) % 360.0) - 180.0
    return math.exp(-((offset / HOLLOW_SIGMA_DEG) ** 2))


#: key -> (southern latitude, northern latitude), for the boundary lookup.
BELT_LATITUDES = {key: (south, north) for key, _name, south, north, _how in BELTS}


def belt_edge(key: str, edge: str, lon_deg: float) -> float:
    """The latitude of one wavy belt boundary at one longitude."""
    south, north = BELT_LATITUDES[key]
    base = south if edge == "south" else north
    if key == "seb" and edge == "south":
        weight = _hollow(lon_deg)
        return base + wave(key, edge, lon_deg) * (1.0 - weight) + HOLLOW_DEPTH_DEG * weight
    return base + wave(key, edge, lon_deg)


# ------------------------------------------------------------- the sectors -
#: How many longitude sectors a wavy belt is cut into, and where the cuts fall.
#: The origin puts the spot's own meridian in the middle of a sector rather
#: than on a seam, so the hollow is drawn by one ring rather than shared
#: between two.
SECTOR_COUNT = 6
SECTOR_SPAN = 360.0 / SECTOR_COUNT
SECTOR_ORIGIN = SPOT_LON - SECTOR_SPAN / 2.0

#: Degrees of longitude between vertices along a wavy boundary.  Six samples
#: the fifth harmonic -- the shortest period any boundary here carries -- twelve
#: times per cycle, and leaves each edge 1.4 mm long, well over the 0.5 mm this
#: set holds a ring edge to.
SECTOR_STEP_DEG = 6.0


def _sector_longitudes(index: int) -> list[float]:
    start = SECTOR_ORIGIN + index * SECTOR_SPAN
    count = int(round(SECTOR_SPAN / SECTOR_STEP_DEG))
    return [start + SECTOR_SPAN * step / count for step in range(count + 1)]


def belt_sector_ring(key: str, index: int) -> list[tuple[float, float]]:
    """One longitude sector of a wavy belt, as a closed (lon, lat) ring.

    Walked west to east along the southern boundary and back east to west along
    the northern one, which is counter-clockwise seen from outside the globe --
    the convention `parts/atlas.py` and `parts/mercury_atlas.py` use.

    Neighbouring sectors share their two seam vertices exactly, so the radial
    plane each throws through that seam is the same plane for both and the
    lenses fuse into one belt along an ordinary flat face.
    """
    longitudes = _sector_longitudes(index)
    south = [(lon, belt_edge(key, "south", lon)) for lon in longitudes]
    north = [(lon, belt_edge(key, "north", lon)) for lon in reversed(longitudes)]
    return [(round(lon, 4), round(lat, 4)) for lon, lat in south + north]


def belt_rings(key: str) -> list[list[tuple[float, float]]]:
    return [belt_sector_ring(key, index) for index in range(SECTOR_COUNT)]


# ------------------------------------------------------------ oval rings ---
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


def _normalise(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


def oval_ring(lat_deg: float, lon_deg: float, semi_lon: float, semi_lat: float,
              count: int) -> list[tuple[float, float]]:
    """A closed oval on the sphere, `semi_lon` by `semi_lat` degrees of arc.

    Walked at `count` even bearings about its own centre, with the angular
    radius at bearing theta -- measured from north, positive toward east --

        r(theta) = a b / sqrt((b sin theta)^2 + (a cos theta)^2)

    which is an ellipse in polar form: r is `semi_lat` due north and `semi_lon`
    due east.  Both semi-axes are degrees of great-circle arc, so the oval is
    the size it says it is whatever latitude it sits at; at -22 that makes its
    longitudinal extent 7.8 per cent wider than its arc.

    Returned counter-clockwise seen from outside the globe, in (longitude,
    latitude) degrees.
    """
    centre = _unit(lon_deg, lat_deg)
    north = (0.0, 0.0, 1.0)
    east = _normalise(_cross(north, centre))
    up = _cross(centre, east)
    ring = []
    for index in range(count):
        theta = -2.0 * math.pi * index / count
        radius = (
            semi_lon * semi_lat
            / math.hypot(semi_lat * math.sin(theta), semi_lon * math.cos(theta))
        )
        reach = math.radians(radius)
        point = tuple(
            math.cos(reach) * centre[axis]
            + math.sin(reach) * (math.cos(theta) * up[axis]
                                 + math.sin(theta) * east[axis])
            for axis in range(3)
        )
        lon, lat = _lon_lat(point)
        ring.append((round(lon, 4), round(lat, 4)))
    return ring


#: Vertex counts, chosen against the 0.50 mm least ring edge this set holds to
#: everywhere -- the margin `parts/mercury_atlas.py` set, a quarter of a nozzle
#: over the 0.40 mm the printer can actually lay down.  The spot's perimeter is
#: 8.09 mm and the collar's 11.04 mm, so 13 and 18 vertices leave shortest
#: edges of 0.51 and 0.54 mm.  Finer is not better here: a 16-vertex spot has
#: 0.42 mm edges at the two flat ends, under that margin, and buys 0.01 mm of
#: fidelity.  At 13 steps the chord falls 0.044 mm inside the true ellipse,
#: which is a ninth of a nozzle.
SPOT_VERTICES = 13
COLLAR_VERTICES = 18

SPOT_RING = oval_ring(SPOT_LAT, SPOT_LON, SPOT_SEMI_ARC_LON,
                      SPOT_SEMI_ARC_LAT, SPOT_VERTICES)
COLLAR_RING = oval_ring(SPOT_LAT, SPOT_LON, COLLAR_SEMI_ARC_LON,
                        COLLAR_SEMI_ARC_LAT, COLLAR_VERTICES)


# ----------------------------------------------------- what markings ask for
def belt_specs():
    """The region specs `parts/markings.py` gives the `bands` marking."""
    specs = []
    for key, _name, south, north, how in BELTS:
        if how == "band":
            specs.append(("band", south, north))
        else:
            specs.append(("outline", belt_rings(key)))
    return specs


def zone_specs():
    """The region specs `parts/markings.py` gives the `zones` marking.

    `shell` rather than `band`: a constant-depth latitude shell, not a lens
    that is deepest in the middle and vanishes at its own edges.  A zone is
    drawn wider than it is shown and trimmed by the belt beside it, so where
    the trim lands must not decide how deep the inlay is -- and a lens floor
    that osculates the depth sphere exactly where an outline belt's floor sits
    is what left an untriangulable sliver on the first build of this
    correction.  `features/patches.py` carries that measurement.
    """
    return [("shell", drawn_south, drawn_north, ZONE_DEPTH)
            for _key, _name, _south, _north, drawn_south, drawn_north in ZONES]


# ------------------------------------------------------------- the record --
#: name -> ring, for the resolution report and for naming a ring in a message.
RINGS = {"spot": SPOT_RING, "collar": COLLAR_RING}
for _key, _name, _s, _n, _how in BELTS:
    if _how == "outline":
        for _index, _ring in enumerate(belt_rings(_key), 1):
            RINGS["%s_sector%d" % (_key, _index)] = _ring

#: Why there is nothing else on this globe, stated here so a later reader finds
#: it before reopening it.  The reference has far more detail than the list
#: above; almost none of it survives a 0.4 mm nozzle and a flush inlay.
NOT_DRAWN = (
    "Jupiter's globe is the largest in the set at Ø%.2f mm, so one degree "
    "of arc is %.4f mm and a %.1f mm nozzle is %.2f degrees of it. The "
    "reference shows white ovals in the temperate belts, polar hoods, festoons "
    "hanging off the North Equatorial Belt, plumes, and fine filamentary "
    "turbulence along every belt edge. None of it is drawn. The white ovals "
    "subtend 2 to 4 degrees, which is one to two nozzle widths with no room "
    "for a boundary either side; the festoons are under a degree wide; the "
    "turbulence is finer again. A marking that narrow prints as a "
    "single-extrusion thread and reads as a print defect, and the set's "
    "material rules forbid deliberate grit. The one irregularity that IS drawn "
    "is the %.1f degree wave on the two widest belt boundaries -- %.2f mm, "
    "over five nozzle widths -- and it is drawn because at that size it is a "
    "shape rather than noise."
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG, WAVE_AMPLITUDE_DEG,
       WAVE_AMPLITUDE_DEG * MM_PER_DEG)
)
