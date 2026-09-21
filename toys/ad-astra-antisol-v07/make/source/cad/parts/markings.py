"""What each world's surface actually shows.

Every marking is a flush colour inlay in the globe's own sphere, described in
the planet's own frame, in angles rather than millimetres.  Describing them
that way is what lets one minimum outline width hold from Mercury to Jupiter,
and it is what makes the same marking correct when the planet is leaning at
its true obliquity.

How a marking is specified depends on what it is, and after Jupiter's
correction the split no longer falls world by world.

Neptune and Uranus are described entirely by latitude, longitude and angular
size, because a belt of latitude and a round patch are what a band system and
a storm actually are.  Jupiter and, since its own correction, Saturn are
described BOTH ways: their narrow belts are still plain latitude bands, but
their two widest each are outline rings carrying a 2.5 degree wave on each
boundary, because an exact circle of latitude reads as a machined edge and
only the widest bands have room for a wave.  Jupiter's Great Red Spot and its
collar are outline ovals as well, and Saturn's bright northern region is a
`cap`.  A belt that encircles the globe is an annulus and no single radial
cone is one, so each wavy belt is six longitude sectors abutting on exact
radial planes.

Earth, Mars, Mercury and Venus are described by outline throughout.  They are
the four worlds in the set with a real mapped surface -- Earth's coastlines,
the dark triangle of Syrtis Major that every telescope owner has drawn since
1659, Mercury's smooth plains with the Caloris basin in them, and Venus's
highland continents under its clouds -- and drawing any of the four as circles
throws that away.  Earth's and Mars's are recognisable silhouettes a player can
check the model against, and so is Aphrodite Terra; Mercury's plains are not,
because its albedo boundaries are soft and unnamed, but circles are still the
one thing they must not be: a union of discs reads as a beach ball rather than
as terrain.  Neptune's dark spot stays a round patch, because a storm in an
atmosphere really is one; Jupiter's is an oval because the real one is half
again wider than it is tall and three overlapping circles read as a lozenge.
Earth's rings live in `parts/atlas.py`, Mars's in `parts/mars_atlas.py`,
Mercury's in `parts/mercury_atlas.py`, Venus's in `parts/venus_atlas.py`,
Jupiter's belts, zones, spot and collar in `parts/jupiter_atlas.py` and
Saturn's five bands, its wave and its northern cap in
`parts/saturn_atlas.py`.

Venus is the only one of the four drawn from radar rather than from anything
the eye could see, because its surface is under an opaque atmosphere and the
Magellan mosaic is the only picture of it there is.

Each entry is (colour, [region specs]).  A region spec is one of
    ("blob",    [(lat, lon, angular_radius), ...])
    ("band",    lat_low, lat_high)              a lens, deepest in the middle
    ("shell",   lat_low, lat_high[, depth])     constant depth edge to edge
    ("outline", [[(lon, lat), ...], ...])       closed rings; Earth, Mars, Mercury
    ("cap",     boundary_lat)                   everything above a parallel

There are two ways for one marking to give way to another, and which is right
depends on which of them wins.  A marking may subtract another one, which is
how Earth's dryland sits inside Earth's land rather than beside it: that is
what a LATER marking's claim on an EARLIER one's material needs.  Those
subtractions happen while the regions are still plain balls and cylinders,
never after they have been sliced into shells: two slices of one shell share
its spherical faces, and a boolean between coincident faces is the one that
fails silently.

The other way is simply to be listed later.  `parts/world.py` splits the globe
one marking at a time and carries the remainder forward, so a marking listed
after another is already trimmed by it and needs no subtraction at all -- and,
unlike a subtraction, that route describes the shared boundary exactly once.
Jupiter's belts, spot, collar and zones are ordered by priority for that
reason, and so are Saturn's bands, its one darker band and its cap -- which
are disjoint in latitude in any case, so neither route has anything to
resolve between them.  Earth's, Mars's, Mercury's and Venus's keep the
subtractions they were built with.
"""

from __future__ import annotations

from parts import atlas as ATLAS
from parts import jupiter_atlas as JUPITER_ATLAS
from parts import mars_atlas as MARS_ATLAS
from parts import mercury_atlas as MERCURY_ATLAS
from parts import saturn_atlas as SATURN_ATLAS
from parts import venus_atlas as VENUS_ATLAS

# name -> ordered list of (marking key, filament, regions, subtract_keys)
MARKINGS = {
    "mercury": [
        # Three-tone albedo map: the smooth plains, and the Caloris basin as a
        # floor with a rim round it.  Rings in `parts/mercury_atlas.py`, beside
        # Earth's and Mars's.
        #
        # The plains keep the seven centres the round-patch build used and
        # keep this one marking key; what changed is the filament and the
        # outline.  cocoa_brown rather than dark_gray because the separation
        # was measured in the canonical render -- the same piece rendered
        # twice at one camera, once in the candidate and once in the globe's
        # own gray, so the pixels that move are the patch and nothing else
        # moves at all.  On those pixels dark_gray #6F6E6D against the gray
        # #9FA19F globe is 21.8 of 255 luma levels at the hero frame and 22.0
        # at the state-sheet frame, and on the smallest ball in the set the
        # patches vanished into the globe at that separation.  cocoa_brown
        # #8E3C06 measures 45.5 and 45.9, a little over twice as far, and
        # stops short of black #000000 at 139.6 and 141.0, which on a small
        # gray ball reads as a hole in the print rather than as terrain.  On
        # the sealed channels the shop prints, the same three are 50.3, 86.9
        # and 160.4.  `measure/mercury-tone-separation.md` is the measurement.
        #
        # Facing, in the form Venus's and Jupiter's comments below use, and
        # for the same reason: the patch is no use on the hidden hemisphere.
        # Dot products against the view axis, hero frame (azimuth -55,
        # elevation 22) then state-sheet frame (-45, 35.264), Sol then
        # Anti-Sol.  Mercury's obliquity is 0.03 degrees, so the mirrored lean
        # moves nothing here and the two armies agree to two decimals.
        #
        #   plain at (18, 24)     +0.28 +0.28 | +0.46 +0.46
        #   plain at (6, 48)      -0.17 -0.17 | +0.02 +0.02
        #   plain at (-22, 118)   -0.99 -0.99 | -0.94 -0.94
        #   plain at (-10, 138)   -0.95 -0.95 | -0.90 -0.90
        #   plain at (38, 205)    +0.10 +0.10 | +0.14 +0.13
        #   plain at (-6, 255)    +0.55 +0.55 | +0.35 +0.35
        #   plain at (2, 162)     -0.73 -0.73 | -0.71 -0.71
        #   Caloris at (30, -50)  +0.99 +0.99 | +0.99 +0.99
        #
        # Three of the seven plains face the hero camera and four face the
        # sheet camera, the best of them at +0.55.  That is a record rather
        # than a repair: unlike Venus's cloud Y and Jupiter's spot, which each
        # sat squarely on the hidden hemisphere and were carried in longitude
        # to fix it, Mercury's plains were never the problem -- the contrast
        # was.  The centres are therefore exactly where they were.
        #
        # Caloris is the one feature here whose longitude is free, and it is
        # placed by that measurement rather than by preference: -50 is the
        # midpoint of the two camera azimuths, which puts the basin 0.99
        # against both view axes on both armies -- the most nearly dead-on any
        # marking in this set gets.  `measure/mercury-facing.md`.
        ("plains", "cocoa_brown", [
            ("outline", MERCURY_ATLAS.PLAINS_RINGS),
        ], ()),
        # The rim is the annulus left when the floor is subtracted out of the
        # outer ring, which is why it is two concentric outlines rather than a
        # circle union: a basin has a raised edge, and a single disc of colour
        # is a painted dot.  Both outlines are scalloped -- a true circle at
        # 4.3 mm reads as a drilled hole or a moulding pip, and the
        # reference's basin edge is visibly scalloped.
        ("caloris_rim", "cocoa_brown", [
            ("outline", [MERCURY_ATLAS.CALORIS_RIM]),
        ], ("caloris_floor",)),
        # The floor is the brightest thing on the reference, brighter than the
        # globe, so it is the one place this world spends a third filament.
        # Measured the same way as the terrain tone, white #FFFEF7 separates
        # 36.9 luma levels from the gray globe against beige #F7E6DE's 35.3,
        # and it leads by more on the boundary a reader actually reads -- the
        # floor against the rim -- at 114.3 against 104.9.  Both clear the
        # 21.8 the vanished dark_gray patches managed by half as much again,
        # so the third filament is worth loading; white is the one that
        # separates furthest.  beige is the set's known weak pair with white,
        # at 9.4 as rendered, but only one of the two is used here, so that
        # pair never occurs on this globe.
        # `measure/mercury-tone-separation.md`.
        ("caloris_floor", "white", [
            ("outline", [MERCURY_ATLAS.CALORIS_FLOOR]),
        ], ()),
        # Still not craters.  The reference shows them everywhere and they are
        # still not drawn: at 13.78 mm one degree of arc is 0.120 mm, so a 0.4
        # mm nozzle is 3.33 degrees and the largest crater outside Caloris is
        # one or two nozzle widths across, with no room for a rim and a floor
        # inside that.  It would print as a single-extrusion pit and read as a
        # print defect.  `parts/mercury_atlas.py`'s CRATERS_NOT_DRAWN carries
        # the number; Caloris is the exception because at 36 degrees of arc it
        # is eleven nozzle widths across.
    ],
    "mars": [
        # Syrtis Major, Mare Acidalium and their neighbours, as outlines.  The
        # six round patches that stood here sat on the right features and in
        # the right places; what was wrong was that they were circles.  Syrtis
        # Major is a dark triangle, the southern maria run together into one
        # belt, and a union of discs says neither.  Not craters -- at this
        # radius a crater reads as a print defect, while the albedo map is
        # what Mars actually looks like from a distance.  The rings are in
        # `parts/mars_atlas.py`, beside Earth's.
        ("albedo", "cocoa_brown", [
            ("outline", MARS_ATLAS.ALBEDO_RINGS),
        ], ()),
        # The two polar caps.  A blob centred on a pole IS a polar cap, so the
        # two blobs and their angular radii are the ones this set already had.
        # What is added is the lobes: left bare, a cap ends on an exact circle
        # of latitude and reads as a lid laid on the globe rather than as ice,
        # so a few lobes are unioned onto each one to break that rim.  The
        # north cap is the larger and the more irregular, as the reference
        # shows.  The caps stay cut back by `albedo`.
        ("caps", "white", [
            ("blob", [(90, 0, MARS_ATLAS.CAP_NORTH_ANGULAR_RADIUS),
                      (-90, 0, MARS_ATLAS.CAP_SOUTH_ANGULAR_RADIUS)]),
            ("outline", MARS_ATLAS.CAP_LOBES),
        ], ("albedo",)),
    ],
    "venus": [
        # The Magellan radar surface: highland provinces in the brighter tone,
        # lowland plains in the darker one.  Rings in `parts/venus_atlas.py`,
        # beside Earth's, Mars's and Mercury's.
        #
        # This world stopped showing its atmosphere and started showing its
        # surface, and that is a decision of the owner of the set rather than a
        # drafting accident.  What stood here was the Mariner-10 ultraviolet
        # cloud Y, ten overlapping `orange` circles on a `beige` globe, and it
        # was deleted for three reasons of which the third decides.  `orange`
        # #FF671F on `beige` #F7E6DE was the highest-contrast pairing anywhere
        # in the set, higher than Jupiter's brown on orange.  Ten overlapping
        # circles do not read as a Y; in `iso.png` they read as one orange
        # smear down the side of a cream ball.  And it was the wrong subject: a
        # cloud pattern and a radar map are two pictures of two different
        # objects, and only one of them can be on the globe.
        #
        # The globe under them moved with them.  `beige` is a pale pink-cream
        # and the reference is a saturated golden amber, which is a gap no
        # marking closes, so the globe is `sunflower_yellow` #FFB549 -- the
        # closest amber in the palette, and already in the set as the Sol den
        # plug, so it costs no new filament.  `measure/venus-tone-separation.md`
        # measures the three tones against each other in the canonical render.
        #
        # Venus is still upside down at 177.36 degrees and this is still the
        # only pattern in the set that reads inverted; the planet frame is what
        # inverts it, and none of the data below is pre-inverted to compensate.
        #
        # Longitudes carry `venus_atlas.LONGITUDE_OFFSET`, +90 degrees, applied
        # to the whole marking set at once.  The old -135 was chosen for the
        # cloud Y and was deleted with it; this number was measured from
        # scratch, in the form Mercury's and Jupiter's comments use.  Dot
        # products against the view axis, hero frame (azimuth -55, elevation
        # 22) then state-sheet frame (-45, 35.264), Sol then Anti-Sol:
        #
        #   Aphrodite Terra   +0.98 +0.97 | +0.94 +0.92
        #   Atalanta Planitia +0.37 +0.33 | +0.10 +0.06
        #   Lada Terra        +0.13 +0.17 | +0.39 +0.43
        #   Phoebe Regio      -0.64 -0.60 | -0.62 -0.56
        #   Themis Regio      -0.34 -0.28 | -0.23 -0.15
        #   Alpha Regio       -0.47 -0.45 | -0.21 -0.19
        #   Ishtar Terra      -0.38 -0.44 | -0.52 -0.58
        #   Beta Regio        -0.81 -0.80 | -0.90 -0.88
        #   Guinevere Plan.   -0.99 -0.99 | -0.94 -0.93
        #
        # Aphrodite is the feature this piece is recognised by, it is the only
        # one on Venus with a silhouette a reader can match against the image,
        # and at +90 all 24 of its vertices are on the near hemisphere at both
        # frames on both armies.  That is what the offset was chosen for; the
        # rest of the map follows it rather than the other way round.
        # `measure/venus-facing.md` is the scan over every offset.
        ("highland", "beige", [
            ("outline", VENUS_ATLAS.HIGHLAND_RINGS),
        ], ()),
        # The plains, with the highlands subtracted out of them, so that where
        # the two overlap the highland wins -- the same structure Earth's
        # `land` and `dryland` use, one level down.
        ("lowland", "cocoa_brown", [
            ("outline", VENUS_ATLAS.LOWLAND_RINGS),
        ], ("highland",)),
        # Not the texture.  The reference is dominated by fine filamentary
        # radar brightness and none of it is here: one degree of arc is 0.1443
        # mm on this globe and the 0.4 mm nozzle needs 2.77 degrees, so a
        # filament a few tens of kilometres wide is a fifth of a nozzle width.
        # `parts/venus_atlas.NOT_DRAWN` carries the arithmetic. No stippling
        # and no fine ribs stand in for it: the set's material rules forbid
        # deliberate grit and at this size it would print as noise.
        #
        # And nothing else: no clouds, no cloud Y, no terminator shading, no
        # craters, no named volcano, no polar cap. The reference is a surface
        # map and shows none of those.
    ],
    "earth": [
        # The Americas, Africa, Eurasia and Australia, as coastlines.  The
        # ordering, the filaments and the subtractions are the ones every
        # other world here uses; only the shape of a region has changed.
        ("land", "green", [
            ("outline", ATLAS.LAND_RINGS),
        ], ("dryland",)),
        ("dryland", "beige", [
            # The Sahara, the Kalahari, inner Asia, the American southwest and
            # the Australian outback: dry interiors, so they sit inside land
            # rather than beside it.
            ("outline", ATLAS.DRYLAND_RINGS),
        ], ()),
        ("ice", "white", [
            # The northern cap encloses the pole and so has no ring; it is the
            # parallel at 72 degrees.  Left bare it ends on an exact circle of
            # latitude and reads as a lid laid on the globe, so the lobes are
            # unioned onto it to break that rim into an ice field.  Greenland
            # joins them as the one ice sheet with a coastline of its own.
            ("cap", ATLAS.ARCTIC_CAP_LAT),
            ("outline", ATLAS.ICE_RINGS),
        ], ("land", "dryland")),
    ],
    "neptune": [
        ("spot", "dark_gray", [
            ("blob", [(-22, 0, 17), (-20, 14, 12)]),
        ], ()),
        ("streaks", "white", [
            ("band", -46, -41),
            ("band", 11, 15),
            ("band", 30, 33),
        ], ()),
    ],
    "uranus": [
        # One faint band.  It runs pole to pole on the visible face because the
        # pole lies 7.77 degrees past horizontal -- the band itself is an
        # ordinary latitude band, and the obliquity turns it upright.
        ("band", "white", [
            ("band", -9, 9),
        ], ()),
    ],
    "saturn": [
        # Five bands, unequal and asymmetric, in a mid tone -- and a bright
        # northern cap.  What stood here was four `cocoa_brown` bands each
        # exactly 12 degrees wide at -51/-39, -21/-9, 9/21 and 39/51: equal
        # width, equal spacing, perfectly symmetric about the equator, and in
        # the highest-contrast pairing in the whole palette.  `cocoa_brown`
        # #8E3C06 on `yellow` #FFD834 read as a hard-striped gold ball, which
        # is the opposite of `ref/saturn-sol.png` -- a cream-to-pale-tan globe
        # whose bands are wide, soft-edged and low in contrast, whose strongest
        # band is barely darker than its neighbours, and whose northern part is
        # lighter than its southern.  This correction runs the opposite way
        # from Jupiter's, Venus's, Mercury's, Mars's and Earth's: Saturn was
        # not too plain, it was too loud.  Keeping it quiet next to Jupiter's
        # loud one is worth having in a set where both stand on the board at
        # once.
        #
        # The band filament was measured rather than chosen, against `yellow`
        # and against the fallback the Wish allows, in the canonical render, in
        # `measure/saturn-tone-separation.md`.  `parts/saturn_atlas.py` draws
        # the latitudes, the wave and the cap, and carries the nozzle
        # arithmetic for everything that is not drawn.
        #
        # Two of the five wave.  The Earth run established that an exact circle
        # of latitude reads as a lathe mark and Jupiter applied it to its two
        # widest belts; the two widest here -- +18/+33 and -14/-30 -- carry a
        # 2.5 degree wave on each boundary, as six longitude sectors abutting
        # on exact radial planes.  The three narrow ones stay plain `band`
        # regions.  A flush inlay still has a hard edge and there is no way to
        # make it soft; the reference's bands fade into each other and this
        # piece's cannot.  Lowering the contrast is the available substitute
        # for softening the edge, which is why the filament matters more than
        # the wave.
        ("bands", SATURN_ATLAS.BAND_COLOUR, SATURN_ATLAS.light_band_specs(), ()),
        # The one band the reference lets you notice, and the only `cocoa_brown`
        # left on this globe: the -14/-30 band, the widest of the five.  It is
        # kept only because it measured as distinguishable without dominating;
        # `measure/saturn-tone-separation.md` carries that measurement and the
        # decision, including what the piece looks like without it.
        ("southbelt", SATURN_ATLAS.DARK_BAND_COLOUR,
         SATURN_ATLAS.dark_band_specs(), ()),
        # The bright northern region, above +58, in the lightest tone this
        # piece already carries.  A plain `cap` and no lobes: the Earth lesson
        # about lids is about a small bright cap on a dark globe, and this is a
        # wide soft brightening on an already light one, where an exact
        # parallel is what the reference shows.  North only, so it shows on the
        # Sol piece and hides on the Anti-Sol one at the product's own frame --
        # the same 26.73 degree lean that already separates the two armies.
        # The pieces remain exact mirrors; it is the camera that differs, and
        # `measure/saturn-cap-visibility.md` measures that rather than leaving
        # it to be reported as a mirror failure.
        ("cap", SATURN_ATLAS.CAP_COLOUR, SATURN_ATLAS.cap_specs(), ()),
        # Nothing else.  No hexagonal polar vortex, no storms, no spokes in the
        # ring, no ring divisions, no ring shadow on the globe.
        # `parts/saturn_atlas.NOT_DRAWN` carries the nozzle arithmetic each of
        # those was rejected on, the hexagon included.
    ],
    "jupiter": [
        # Six belts, as before, so the print cost does not change -- but at
        # Jupiter's real latitudes, which are neither evenly spaced nor
        # symmetric: +24/+31, +7/+17, -7/-20, -27/-34, +38/+43, -40/-46.
        # What stood here was six bands each exactly 12 degrees wide, equally
        # spaced and perfectly symmetric about the equator, and that is a beach
        # ball: regularity is the single thing that tells a viewer they are
        # looking at a manufactured object rather than at a planet.  The
        # reference's bands differ in width by a factor of three.
        #
        # The two widest -- South Equatorial at 13 degrees and North Equatorial
        # at 10 -- are `outline` rings rather than `band` regions, because the
        # Earth run established that an exact circle of latitude reads as a
        # machined edge, and they carry a 2.5 degree wave on both boundaries.
        # The other four stay plain bands: at 5 to 7 degrees wide a wave would
        # eat the band.  A belt that encircles the globe is an annulus and no
        # single radial cone is one, so each wavy belt is six longitude sectors
        # that abut on exact radial planes and fuse back into one body.
        # `parts/jupiter_atlas.py` draws all of it.
        #
        # The belts subtract nothing.  The spot and its collar are kept clear
        # of them by the hollow the South Equatorial Belt's southern boundary
        # bends into, and where the collar reaches past -27 it is the COLLAR
        # that gives way, so the South Temperate Belt stays the plain band it
        # is declared to be.
        ("bands", "cocoa_brown", JUPITER_ATLAS.belt_specs(), ()),
        # The Great Red Spot, as one oval rather than three overlapping
        # circles.  Three circles read as a lozenge; the reference is a clean
        # oval, wider than it is tall.  16000 by 11000 km on a planet 139820 km
        # across is 13 degrees of arc by 9 -- half again wider than tall, and
        # not the long thin oval of nineteenth-century drawings, because the
        # spot has been shrinking for a century.
        #
        # The latitude is the real one.  The longitude is free, because Jupiter
        # turns in ten hours and this set fixes no meridian, and the existing
        # -110 degree carry that puts it in front of the camera in both
        # photographed frames is preserved exactly: the spot's centre is still
        # longitude -48.  Re-measured against the oval rather than the blobs,
        # dot products against the view axis, hero frame (azimuth -55,
        # elevation 22) then state-sheet frame (-45, 35.264), Sol then
        # Anti-Sol:
        #
        #   spot centre (-22, -48)   +0.69 +0.74 | +0.51 +0.57
        #   worst ring vertex         +0.63 +0.68 | +0.44 +0.50
        #
        # `measure/jupiter-facing.md` carries the whole table, every vertex of
        # both ovals included.
        ("spot", "red", [
            ("outline", [JUPITER_ATLAS.SPOT_RING]),
        ], ()),
        # The collar: a second ring just outside the red one, so the spot has
        # an edge rather than floating.  The same structure Mercury's Caloris
        # rim uses -- an outer ring with the inner one subtracted out of it --
        # and the same filament as the belts, so it adds no fourth colour.
        #
        # Drawn as the whole oval and trimmed by the same split order: the spot
        # and the belts are both cut before it, so what is left of the collar
        # ring is the annulus outside the red oval and outside the South
        # Temperate Belt.  The spot is 9 degrees tall centred at -22 and the
        # South Tropical Zone is only 7 degrees deep, so a collar wide enough
        # to print at all reaches past -27 into that belt.  Rather than bite a
        # second hollow out of a belt the correction requires to stay a plain
        # latitude band, the collar gives way there and the two cocoa regions
        # simply meet, over 12 degrees of longitude and 1.5 of latitude.
        # `measure/jupiter-atlas-resolution.md` measures that.
        ("collar", "cocoa_brown", [
            ("outline", [JUPITER_ATLAS.COLLAR_RING]),
        ], ()),        # The bright zones: the third tone, and the thing whose absence cost
        # this world its rhythm.  The reference is three-toned -- a base
        # colour, darker belts AND bright cream zones between them -- and the
        # build was two-toned, so the bright zones were bare globe.
        #
        # `beige` #F7E6DE, measured rather than chosen: against the `orange`
        # #FF671F globe and against the `cocoa_brown` #8E3C06 belts, in the
        # greyscale of the canonical render, in
        # `measure/jupiter-tone-separation.md`.  `sunflower_yellow` was the
        # nearest rival and was refused there on two grounds, one measured and
        # one about the set: it is the narrowest separation of the four
        # candidates, and since the Venus correction it is Venus's whole globe
        # as well as the Sol den plug, so a third job would have been the one
        # that broke it.  `yellow` is Saturn's globe.  `white` measures
        # furthest of all and was not taken because it is already the brightest
        # feature on four other worlds here.
        #
        # Each zone is drawn as a latitude band WIDER than it ends up, running
        # several degrees into the belts on either side, and it is the split
        # order that trims it: `parts/world.py` carves the markings out of the
        # globe one key at a time and carries the remainder forward, so by the
        # time the zones are cut the belts, and the material under them, are
        # already gone.  A zone boundary is therefore literally the face the
        # belt's own cut left behind -- including on the two boundaries that
        # wave and the one that bends round the spot -- and it cannot drift
        # from it by so much as a rounding error.
        #
        # This is deliberately NOT the `subtract` route Earth's `dryland` takes
        # out of `land`.  That route exists to let a LATER marking win over an
        # earlier one, and it necessarily describes the shared boundary twice:
        # once as the belt lens the globe was split by, and once as the solid
        # cone subtracted from the zone.  Measured here, the two descriptions
        # differed by about a ten-thousandth of a millimetre and left a
        # 0.0016 mm2 spline sliver of bare globe along the North Equatorial
        # Belt's northern boundary -- a face with no area to triangulate, which
        # took the whole set's renderer down with `NbNodes` on a null
        # triangulation.  Splitting in priority order describes the boundary
        # once.
        ("zones", JUPITER_ATLAS.ZONE_COLOUR, JUPITER_ATLAS.zone_specs(), ()),

    ],
}
