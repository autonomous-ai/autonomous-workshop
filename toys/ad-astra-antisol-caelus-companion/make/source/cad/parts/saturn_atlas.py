"""Saturn's band system and its bright northern cap.

Saturn used to wear four `cocoa_brown` latitude bands, every one of them
exactly 12 degrees wide, at -51/-39, -21/-9, 9/21 and 39/51.  Equal width,
equal spacing, perfectly symmetric about the equator -- the same regularity
Jupiter's correction removed, and the same beach ball.  It also wore the
wrong contrast: `cocoa_brown` #8E3C06 against `yellow` #FFD834 is one of the
highest-contrast pairings in the whole palette, so the piece read as a hard
striped gold ball.

`ref/saturn-sol.png` is the softest image in the reference set.  Its globe
runs cream to pale tan; its bands are wide, soft-edged and low in contrast;
the strongest one is barely darker than its neighbours; and the northern part
of the globe is lighter than the southern.  Saturn is the quiet planet next to
Jupiter's loud one, and this correction runs the opposite way from the last
three: Saturn was not too plain, it was too loud.

Three things are drawn here, and one arithmetic decides all three: Saturn's
globe is Ø26.00 mm, so one degree of arc is 0.2269 mm and the 0.4 mm nozzle is
1.76 degrees of it.  `measure/saturn-atlas-resolution.md` checks every band
width, every ring edge and every neck against that number.

**Five bands, unequal and asymmetric.**  +46/+55, +18/+33, +2/+10, -14/-30 and
-38/-50.  Their widths are 9, 15, 8, 16 and 12 degrees; no two of the gaps
between them are equal and no pair is a mirror of another.  Five bands in a
cheaper colour is still a simpler print than four in the loudest one.

**The two widest bands wave.**  The Earth run established that an exact circle
of latitude reads as a lathe mark, and Jupiter applied it to its two widest
belts.  The same applies here to +18/+33 and -14/-30, which carry a 2.5 degree
wave on each boundary.  The three narrow bands stay plain `band` regions: at 8
to 12 degrees a wave eats the band.  A belt that encircles the globe is an
annulus and no single radial cone is one, so each wavy band is six longitude
sectors that abut on exact radial planes and fuse back into one body.

**The northern third is lighter.**  A plain `cap` above +58, in the lightest
tone this piece already carries.  It gets no lobed rim: the Earth lesson about
lids is about a small bright cap on a dark globe, and this is a wide soft
brightening on an already light one, where an exact parallel is what the
reference shows.

Nothing here touches Saturn's ring system.  `RING_INNER_D`, `RING_OUTER_D`,
`RING_THICKNESS`, `RING_GLOBE_BITE`, `RING_WEB_SECTORS`, `RING_WEB_INNER_R`,
`RING_WEB_OVERLAP`, `RING_WEB_DROP` and `RING_WEB_SLOPE` are exactly where the
published set left them.  The ring is the one feature on this piece that
already worked, it is what `LADDER_CONSTANT` was solved against, and it
carries the whole set's size ladder.
"""

from __future__ import annotations

import math

import params as P

#: The globe these features are drawn for, and what one degree of it is worth.
GLOBE_D = P.globe_diameter("saturn")                  # 26.00 mm
MM_PER_DEG = math.radians(1.0) * (GLOBE_D / 2.0)      # 0.2269 mm
NOZZLE_DEG = P.NOZZLE_MM / MM_PER_DEG                 # 1.76 degrees of arc

#: Saturn's real equatorial diameter, and the kilometres one degree of arc on
#: it is worth.  This is the arithmetic the rejected hexagon is measured with.
DIAMETER_KM = P.PLANETS["saturn"]["d_km"]             # 116460 km
KM_PER_DEG = math.pi * DIAMETER_KM / 360.0            # 1016.3 km


# ------------------------------------------------------------- the bands ---
#: (key, name, southern latitude, northern latitude, how it is drawn, tone).
#:
#: Read the widths rather than the names: 9, 15, 8, 16, 12.  No two of the
#: pairs are mirror images, no two gaps between them are equal, and the
#: pattern does not repeat -- which is the whole point of the correction.
#:
#: `tone` is "light" for the four bands that print in the band filament and
#: "dark" for the single band allowed to be `cocoa_brown`.  Which one is dark
#: is fixed by the Wish: the -14/-30 band, the widest of the five.
BANDS = (
    ("npb", "North Polar Band", 46.0, 55.0, "band", "light"),
    ("ntb", "North Temperate Band", 18.0, 33.0, "outline", "light"),
    ("eqb", "Equatorial Band", 2.0, 10.0, "band", "light"),
    ("stb", "South Temperate Belt", -30.0, -14.0, "outline", "dark"),
    ("ssb", "South South Band", -50.0, -38.0, "band", "light"),
)

#: Where the bright polar region starts.  The reference brightens toward the
#: north pole and shows an ordinary parallel there rather than an ice edge, so
#: this is a plain cap with no lobes on it.
#:
#: North only.  Saturn's obliquity is 26.73 degrees and the Sol piece leans its
#: north pole toward the camera at the product's own frame, so the cap shows on
#: the Sol piece and hides on the Anti-Sol one.  The two pieces are still exact
#: mirrors of one another; it is the camera that differs, and
#: `measure/saturn-cap-visibility.md` measures exactly that rather than leaving
#: a later reader to report it as a mirror failure.
CAP_LAT = 58.0

#: How far the cap's boundary stands clear of the band below it: 58 - 55 = 3
#: degrees, 0.68 mm, 1.70 nozzle widths of bare globe.  Named here because it
#: is the tightest gap on this globe and the resolution report checks it.
CAP_CLEARANCE_DEG = CAP_LAT - BANDS[0][3]


# ----------------------------------------------------------- the filaments -
#: The four light bands.  `sunflower_yellow` #FFB549 is the Wish's own first
#: choice: a genuine mid tone between `yellow` #FFD834 and the dark browns,
#: already in the set -- the Sol den plug, and since the Venus correction the
#: whole of Venus's globe -- so it costs no new spool.  `beige` #F7E6DE is the
#: fallback the Wish allows if that tone is too close to the globe to see at
#: all, or if Saturn ends up reading as a large Venus.
#: `measure/saturn-tone-separation.md` and
#: `measure/venus-saturn-separation.md` are where the two questions are
#: answered on measured pixels rather than on the catalogue hex, and this
#: constant records which answer was taken.
BAND_COLOUR = "sunflower_yellow"

#: The one darker band, if it survives measurement.  `cocoa_brown` #8E3C06 is
#: the loudest pairing this globe can make, so it is held to one band -- the
#: -14/-30, the widest of the five -- and kept only on the evidence in
#: `measure/saturn-tone-separation.md`.
DARK_BAND_COLOUR = "cocoa_brown"

#: The bright northern cap: the lightest tone this piece already carries.
#: `white` #FFFEF7 is Saturn's ring, so the cap loads no new spool either.
CAP_COLOUR = "white"


# --------------------------------------------------------------- the wave --
#: How far a wavy band boundary departs from its own circle of latitude, at
#: most, in degrees.  The brief asks for two or three: enough to take the lathe
#: look off the edge, not enough to read as turbulence.  At 2.5 degrees that is
#: 0.57 mm on this globe, over one nozzle width, so it is a shape rather than
#: noise.
#:
#: Each boundary carries two harmonics of longitude with different periods and
#: phases, so no two of the four boundaries move together and the pattern does
#: not repeat round the globe.  The numbers are deliberately not Jupiter's: the
#: two planets stand on the same board and a shared wave would read as one
#: pattern printed twice.
WAVE_AMPLITUDE_DEG = 2.5

#: boundary -> ((harmonic, amplitude, phase degrees), ...), summed as
#: `amplitude * sin(harmonic * longitude + phase)`.  Each pair totals
#: WAVE_AMPLITUDE_DEG.
WAVES = {
    ("ntb", "south"): ((3, 1.4, 35.0), (5, 1.1, 200.0)),
    ("ntb", "north"): ((2, 1.6, 150.0), (4, 0.9, 305.0)),
    ("stb", "south"): ((2, 1.5, 265.0), (5, 1.0, 80.0)),
    ("stb", "north"): ((3, 1.3, 95.0), (4, 1.2, 20.0)),
}


def wave(key: str, edge: str, lon_deg: float) -> float:
    """The departure of one band boundary from its own parallel, in degrees."""
    return sum(
        amplitude * math.sin(math.radians(harmonic * lon_deg + phase))
        for harmonic, amplitude, phase in WAVES[(key, edge)]
    )


#: key -> (southern latitude, northern latitude), for the boundary lookup.
BAND_LATITUDES = {key: (south, north) for key, _n, south, north, _h, _t in BANDS}


def band_edge(key: str, edge: str, lon_deg: float) -> float:
    """The latitude of one wavy band boundary at one longitude."""
    south, north = BAND_LATITUDES[key]
    base = south if edge == "south" else north
    return base + wave(key, edge, lon_deg)


# ------------------------------------------------------------- the sectors -
#: How many longitude sectors a wavy band is cut into, and where the cuts fall.
#: Six sectors of 60 degrees keeps every vertex about 30 degrees from its own
#: sector's axis, well inside the 72 degree limit `features/patches.py` holds
#: its outline construction to.
#:
#: The origin puts the canonical frame's own central meridian, -55, in the
#: middle of a sector rather than on a seam, so the face a reader is shown is
#: drawn by one ring instead of shared between two.
SECTOR_COUNT = 6
SECTOR_SPAN = 360.0 / SECTOR_COUNT
SECTOR_ORIGIN = -85.0

#: Degrees of longitude between vertices along a wavy boundary.  Six samples
#: the fifth harmonic -- the shortest period any boundary here carries -- twelve
#: times per cycle, and leaves each edge about 1.2 mm long, well over the
#: 0.50 mm this set holds a ring edge to.
SECTOR_STEP_DEG = 6.0


def _sector_longitudes(index: int) -> list[float]:
    start = SECTOR_ORIGIN + index * SECTOR_SPAN
    count = int(round(SECTOR_SPAN / SECTOR_STEP_DEG))
    return [start + SECTOR_SPAN * step / count for step in range(count + 1)]


def band_sector_ring(key: str, index: int) -> list[tuple[float, float]]:
    """One longitude sector of a wavy band, as a closed (lon, lat) ring.

    Walked west to east along the southern boundary and back east to west along
    the northern one, which is counter-clockwise seen from outside the globe --
    the convention the rest of this set's atlases use.

    Neighbouring sectors share their two seam vertices exactly, so the radial
    plane each throws through that seam is the same plane for both and the
    lenses fuse into one band along an ordinary flat face.
    """
    longitudes = _sector_longitudes(index)
    south = [(lon, band_edge(key, "south", lon)) for lon in longitudes]
    north = [(lon, band_edge(key, "north", lon)) for lon in reversed(longitudes)]
    return [(round(lon, 4), round(lat, 4)) for lon, lat in south + north]


def band_rings(key: str) -> list[list[tuple[float, float]]]:
    return [band_sector_ring(key, index) for index in range(SECTOR_COUNT)]


# ----------------------------------------------------- what markings ask for
def _specs_for(tone: str):
    specs = []
    for key, _name, south, north, how, band_tone in BANDS:
        if band_tone != tone:
            continue
        if how == "band":
            specs.append(("band", south, north))
        else:
            specs.append(("outline", band_rings(key)))
    return specs


def light_band_specs():
    """The four bands that print in the band filament."""
    return _specs_for("light")


def dark_band_specs():
    """The single band allowed to be `cocoa_brown`, if it survives measurement.

    `measure/saturn-tone-separation.md` is where it is measured against both
    the globe and the light bands, and where the decision is recorded.
    """
    return _specs_for("dark")


def cap_specs():
    """The bright northern region, as one plain parallel with no lobes."""
    return [("cap", CAP_LAT)]


# ------------------------------------------------------------- the record --
#: name -> ring, for the resolution report and for naming a ring in a message.
RINGS = {}
for _key, _name, _s, _n, _how, _t in BANDS:
    if _how == "outline":
        for _index, _ring in enumerate(band_rings(_key), 1):
            RINGS["%s_sector%d" % (_key, _index)] = _ring


#: Saturn's hexagon, measured rather than argued about.  It is real, it is at
#: the north pole -- which is the pole this piece is looked at from -- and it
#: is still not drawn.
#:
#: The hexagon is about 29,000 km across.  At 1016.3 km per degree of arc that
#: is 28.5 degrees, 6.47 mm on this globe, so the FIGURE would fit.  What does
#: not fit is the line.  The hexagon is a jet-stream boundary a few hundred
#: kilometres wide: take the brightest published estimate of its visible edge,
#: 500 km, and that is 0.49 degrees of arc, 0.11 mm -- a quarter of one nozzle
#: width.  The 0.4 mm nozzle needs 1.76 degrees, 1792 km, three and a half
#: times the widest reading of the feature.  Drawn at the width the printer can
#: actually lay down it would be four times too fat and would read as a
#: moulding line round the pole; drawn at the width it really is, it cannot be
#: printed at all.
HEXAGON_SPAN_KM = 29000.0
HEXAGON_EDGE_KM = 500.0
HEXAGON_SPAN_DEG = HEXAGON_SPAN_KM / KM_PER_DEG
HEXAGON_EDGE_DEG = HEXAGON_EDGE_KM / KM_PER_DEG

#: The ring divisions, on the same footing.  The printed ring is a plain
#: annulus that projects `RING_OUTER_D/2 - globe radius` = 2.00 mm beyond the
#: globe, and that 2.00 mm stands for the whole visible ring system: the C
#: ring's inner edge at 74,658 km of planetary radius out to the A ring's outer
#: edge at 136,775 km, 62,117 km of real ring.  So one millimetre of printed
#: ring is 31,059 km, and the Cassini division -- the one division a naked eye
#: has ever seen -- is 4,700 km of it.
RING_SPAN_KM = 136775.0 - 74658.0                     # 62117 km
RING_PROJECTION_MM = P.RING_OUTER_D / 2.0 - P.globe_radius("saturn")   # 2.00 mm
KM_PER_RING_MM = RING_SPAN_KM / RING_PROJECTION_MM
CASSINI_KM = 4700.0
ENCKE_KM = 325.0
CASSINI_MM = CASSINI_KM / KM_PER_RING_MM
ENCKE_MM = ENCKE_KM / KM_PER_RING_MM

#: Why there is nothing else on this globe, stated here so a later reader finds
#: it before reopening it.
NOT_DRAWN = (
    "Saturn's globe is \u00d8%.2f mm, so one degree of arc is %.4f mm and a "
    "%.1f mm nozzle is %.2f degrees of it. Considered and rejected, with the "
    "arithmetic each was rejected on. The north polar hexagon: it is real, and "
    "it is at the pole this piece is looked at from, which is exactly why it "
    "was considered. It spans %.0f km, %.1f degrees of arc, %.2f mm -- the "
    "figure would fit. Its visible edge would not. That edge is a jet-stream "
    "boundary; at the widest published reading, %.0f km, it is %.2f degrees or "
    "%.2f mm, a quarter of one nozzle width, and the nozzle needs %.2f degrees "
    "or %.0f km, three and a half times the feature. Printed at the width the "
    "printer can lay down it is four times too fat and reads as a moulding "
    "line round the pole; printed at the width it really is, it cannot be "
    "printed at all. The polar vortex eye inside it is finer again. The Great "
    "White Spot storms appear once a Saturnian year and are not what the "
    "reference shows. Spokes in the ring are a transient radial shadowing, "
    "light rather than material, and a solid annulus cannot carry them. The "
    "ring divisions: the printed ring projects %.2f mm beyond the globe and "
    "that stands for %.0f km of real ring, so one millimetre of it is %.0f km; "
    "the Cassini division at %.0f km is %.2f mm and the Encke gap at %.0f km "
    "is %.3f mm, against a %.1f mm nozzle. And the shadow the ring casts on "
    "the globe is light rather than material: printed it becomes a permanent "
    "dark band, which is the opposite of the soft low-contrast surface this "
    "correction exists to produce. No stippling and no fine ribs stand in for "
    "any of them: the set's material rules forbid deliberate grit and at this "
    "size it would print as noise."
    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG,
       HEXAGON_SPAN_KM, HEXAGON_SPAN_DEG, HEXAGON_SPAN_DEG * MM_PER_DEG,
       HEXAGON_EDGE_KM, HEXAGON_EDGE_DEG, HEXAGON_EDGE_DEG * MM_PER_DEG,
       NOZZLE_DEG, NOZZLE_DEG * KM_PER_DEG,
       RING_PROJECTION_MM, RING_SPAN_KM, KM_PER_RING_MM,
       CASSINI_KM, CASSINI_MM, ENCKE_KM, ENCKE_MM, P.NOZZLE_MM)
)
