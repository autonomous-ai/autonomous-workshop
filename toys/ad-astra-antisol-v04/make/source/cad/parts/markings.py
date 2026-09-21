"""What each world's surface actually shows.

Every marking is a flush colour inlay in the globe's own sphere, described in
the planet's own frame, in angles rather than millimetres.  Describing them
that way is what lets one minimum outline width hold from Mercury to Jupiter,
and it is what makes the same marking correct when the planet is leaning at
its true obliquity.

Five of the eight worlds are described by latitude, longitude and angular
size, because a union of round patches or a belt of latitude is what a cloud
pattern, a band system or a storm actually is.  Venus, Neptune, Uranus,
Saturn and Jupiter are those five.

Earth, Mars and Mercury are the three exceptions and are described by
outline.  They are the three worlds in the set with a real mapped surface --
Earth's coastlines, the dark triangle of Syrtis Major that every telescope
owner has drawn since 1659, and Mercury's smooth plains with the Caloris
basin in them -- and drawing any of the three as circles throws that away.
The first two are recognisable silhouettes a player can check the model
against; Mercury's plains are not, because its albedo boundaries are soft and
unnamed, but circles are still the one thing they must not be: a union of
discs reads as a beach ball rather than as terrain.  Jupiter's Great Red Spot
and Neptune's dark spot stay round, because a storm in an atmosphere really is
a round patch.  Earth's rings live in `parts/atlas.py`, Mars's in
`parts/mars_atlas.py` and Mercury's in `parts/mercury_atlas.py`.

Each entry is (colour, [region specs]).  A region spec is one of
    ("blob",    [(lat, lon, angular_radius), ...])
    ("band",    lat_low, lat_high)
    ("outline", [[(lon, lat), ...], ...])       closed rings; Earth, Mars, Mercury
    ("cap",     boundary_lat)                   everything above a parallel
and a marking may subtract another one, which is how Earth's dryland sits
inside Earth's land rather than beside it.  Those subtractions happen while the
regions are still plain balls and cylinders, never after they have been sliced
into shells: two slices of one shell share its spherical faces, and a boolean
between coincident faces is the one that fails silently.
"""

from __future__ import annotations

from parts import atlas as ATLAS
from parts import mars_atlas as MARS_ATLAS
from parts import mercury_atlas as MERCURY_ATLAS

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
        # The Mariner-10 ultraviolet cloud Y.  Venus is upside down at 177.36
        # degrees, so this is the only pattern in the set that reads inverted,
        # and the planet frame is what inverts it.
        # Longitudes carry a -135 degree offset from the pattern's own meridian.
        # Venus has no fixed prime meridian in this set, and at the two frames
        # the product is photographed from -- the iso at -45/35.3 and the Wish's
        # fixed frame at -35/22 -- the unoffset pattern sat on the far
        # hemisphere and no view in the evidence showed any of it.  Measured
        # after the shift: eight of the ten patches face the camera in both
        # frames on both armies, worst patch 0.03 against the view axis.
        ("ypattern", "orange", [
            ("blob", [(-46, -135, 13), (-30, -135, 13), (-14, -135, 13), (0, -135, 13),
                      (14, -117, 12), (26, -101, 11), (36, -83, 10),
                      (14, -153, 12), (26, -169, 11), (36, 173, 10)]),
        ], ()),
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
        ("bands", "cocoa_brown", [
            ("band", -51, -39),
            ("band", -21, -9),
            ("band", 9, 21),
            ("band", 39, 51),
        ], ()),
    ],
    "jupiter": [
        ("bands", "cocoa_brown", [
            ("band", -56, -44),
            ("band", -36, -24),
            ("band", -16, -4),
            ("band", 4, 16),
            ("band", 24, 36),
            ("band", 44, 56),
        ], ("spot",)),
        # The Great Red Spot's latitude is the real one; its longitude is free,
        # because Jupiter turns in ten hours and this set fixes no meridian.
        # Carried -110 degrees from where it started so that it faces the
        # camera in both photographed frames: measured 0.49 against the view
        # axis at worst, against -0.49 before the shift, where it sat squarely
        # on the hidden hemisphere of both Jupiters in every rendered view.
        ("spot", "red", [
            ("blob", [(-22, -48, 13), (-22, -36, 11), (-22, -60, 11)]),
        ], ()),
    ],
}
