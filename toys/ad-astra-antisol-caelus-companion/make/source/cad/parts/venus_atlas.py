"""Venus's highland and lowland provinces, as closed lon/lat rings.

The fourth outline atlas in this set, beside `parts/atlas.py` for Earth's
coastlines, `parts/mars_atlas.py` for Mars's classical albedo map and
`parts/mercury_atlas.py` for Mercury's smooth plains.  It is the one drawn
from radar rather than from anything an eye or a telescope could see: Venus's
surface is under an opaque atmosphere, and the only picture of it is the
Magellan global radar mosaic in `ref/venus-radar-surface.png`.

Longitudes are Venusian east, 0-360, carried verbatim from the atlas supplied
with this revision.  Where a ring crosses the prime meridian its longitudes
continue past 360 -- 350, 360, 374 -- because `features.patches.outline_tool`
works in 3-D directions and knows no seam.  Latitudes are degrees north.

These are stylised silhouettes of the major highland and lowland provinces at
the accuracy a Ø16.53 mm globe can hold, not Magellan mapping.  The names are
the real ones so that a reader can check them.

**The globe is upside down and stays that way.**  Venus's obliquity is 177.36
degrees, so `features.patches.planet_frame` turns this data over and Venus is
the only world in the set whose pattern reads inverted.  Every ring below is
in ordinary Venusian latitude and longitude; nothing here is pre-inverted to
compensate, and the frame is what does the inverting.

`LONGITUDE_OFFSET` is the one number here that is a camera decision rather
than a datum; `parts/markings.py` records why, and
`measure/venus-facing.md` is the measurement it was taken on.
"""

from __future__ import annotations

# ----------------------------------------------------------- highlands ----
#: The long sinuous equatorial highland that dominates the reference.  It
#: spans more than 150 degrees of longitude, and it is the only feature on
#: Venus with a silhouette a reader can match against the image.
APHRODITE_TERRA = [
    (60, -12), (75, -4), (88, 2), (100, 0), (112, -6), (124, -12),
    (138, -14), (152, -10), (166, -4), (180, 2), (194, 6), (206, 10),
    (212, 4), (202, -2), (188, -8), (174, -14), (160, -20), (146, -24),
    (132, -26), (118, -24), (104, -18), (90, -14), (76, -18), (64, -20),
]

#: Aphrodite as the build draws it: two rings that overlap across 28 degrees
#: of longitude and whose union is `APHRODITE_TERRA` exactly.
#:
#: The split is a construction requirement, not a change to the feature.
#: `features.patches._radial_prism` builds an outline as the radial cone
#: through its ring, and its `_OUTLINE_MAX_HALF` refuses a ring whose vertices
#: reach more than 72 degrees from the ring's own mean axis -- past that a
#: vertex's radial line runs nearly parallel to the tool's section planes and
#: the construction stops being well conditioned.  Aphrodite as drawn reaches
#: 77.23 degrees.  Cut in two it reaches 42.68 and 48.45, and because the two
#: halves overlap, both cut chords lie inside the union and neither is a
#: boundary of the highland.  No vertex moved and no width changed:
#: `measure/venus-atlas-resolution.md` measures the undivided ring and the two
#: build rings side by side, and `SIMPLIFIED` records it.
APHRODITE_WEST = [
    (60, -12), (75, -4), (88, 2), (100, 0), (112, -6), (124, -12), (138, -14),
    (146, -24), (132, -26), (118, -24), (104, -18), (90, -14), (76, -18),
    (64, -20),
]

APHRODITE_EAST = [
    (124, -12), (138, -14), (152, -10), (166, -4), (180, 2), (194, 6),
    (206, 10), (212, 4), (202, -2), (188, -8), (174, -14), (160, -20),
    (146, -24), (132, -26), (118, -24),
]

ISHTAR_TERRA = [
    (335, 58), (350, 64), (370, 70), (395, 74), (420, 76), (445, 74),
    (468, 68), (480, 62), (470, 56), (445, 54), (418, 55), (390, 56),
    (365, 56), (348, 55),
]

BETA_REGIO = [
    (276, 20), (280, 32), (288, 36), (294, 30), (292, 20), (284, 15),
]

PHOEBE_REGIO = [
    (274, -14), (278, -4), (288, 0), (294, -8), (288, -16), (280, -18),
]

ALPHA_REGIO = [
    (356, -30), (360, -22), (368, -19), (374, -25), (370, -33), (362, -34),
]

THEMIS_REGIO = [
    (276, -40), (280, -32), (288, -31), (292, -38), (286, -44), (279, -44),
]

LADA_TERRA = [
    (350, -62), (370, -56), (392, -54), (414, -58), (420, -66), (400, -72),
    (376, -73), (356, -69),
]

# ------------------------------------------------------------ lowlands ----
ATALANTA_PLANITIA = [
    (142, 34), (158, 44), (176, 52), (196, 54), (208, 46), (206, 34),
    (192, 28), (172, 26), (154, 28),
]

GUINEVERE_PLANITIA = [
    (300, 12), (312, 24), (328, 32), (346, 32), (356, 24), (352, 12),
    (336, 6), (318, 6),
]

LAVINIA_PLANITIA = [
    (336, -48), (348, -38), (364, -34), (378, -38), (378, -48), (364, -55),
    (346, -55),
]


# ------------------------------------------------------- the offset -------
#: Degrees of Venusian east added to every ring before it is built, applied to
#: the whole marking set at once so the map turns as one piece.
#:
#: Venus fixes no prime meridian in this set, and the old build carried -135
#: degrees for the Mariner-10 cloud Y.  That pattern is deleted and its number
#: carries no authority over this data, so this one was measured from scratch:
#: +90 is the offset that puts Aphrodite Terra most squarely in front of the
#: camera at both photographed frames on both armies, and at it every one of
#: Aphrodite's 24 vertices is on the near hemisphere in all four of those
#: cases.  `measure/venus-facing.md` is the scan.
LONGITUDE_OFFSET = 90.0


def offset(ring):
    """One ring carried by `LONGITUDE_OFFSET`, in the ring's own units."""
    return [(lon + LONGITUDE_OFFSET, lat) for lon, lat in ring]


#: name -> ring as drawn, for the resolution report and for naming a ring in a
#: message.  `aphrodite_terra` is the undivided feature; the two build rings
#: are listed beside it because the report measures all three.
RINGS = {
    "aphrodite_terra": APHRODITE_TERRA,
    "aphrodite_west": APHRODITE_WEST,
    "aphrodite_east": APHRODITE_EAST,
    "ishtar_terra": ISHTAR_TERRA,
    "beta_regio": BETA_REGIO,
    "phoebe_regio": PHOEBE_REGIO,
    "alpha_regio": ALPHA_REGIO,
    "themis_regio": THEMIS_REGIO,
    "lada_terra": LADA_TERRA,
    "atalanta_planitia": ATALANTA_PLANITIA,
    "guinevere_planitia": GUINEVERE_PLANITIA,
    "lavinia_planitia": LAVINIA_PLANITIA,
}

#: The names the build actually sweeps, in build order.
HIGHLAND_NAMES = [
    "aphrodite_west", "aphrodite_east", "ishtar_terra", "beta_regio",
    "phoebe_regio", "alpha_regio", "themis_regio", "lada_terra",
]
LOWLAND_NAMES = ["atalanta_planitia", "guinevere_planitia", "lavinia_planitia"]

HIGHLAND_RINGS = [offset(RINGS[name]) for name in HIGHLAND_NAMES]
LOWLAND_RINGS = [offset(RINGS[name]) for name in LOWLAND_NAMES]


#: What the radar mosaic shows and this globe does not carry, with the reason.
#: These are not omissions of the supplied atlas -- the atlas is a province
#: map and never had them -- but they are the loudest thing in the reference,
#: so they are stated rather than left for a reader to notice.
NOT_DRAWN = {
    "the radar filaments": (
        "tesserae, lava channels, fracture belts and the ragged bright texture "
        "that makes the reference look like beaten gold. The globe is Ø16.53 mm, "
        "so one degree of arc is 0.1443 mm and the 0.4 mm nozzle is 2.77 degrees "
        "of arc. A radar filament a few tens of kilometres wide is 0.2 to 0.5 "
        "degrees on a planet 12,104 km across, a fifth of one nozzle width. None "
        "of it survives, and none of it is approximated: the set's material rules "
        "forbid deliberate grit, and stippling or fine ribs at this size print as "
        "noise rather than as texture"
    ),
    "craters": (
        "Venus has about a thousand and the largest, Mead, is 270 km across, "
        "which is 1.3 degrees of arc and 0.18 mm here -- under half a nozzle "
        "width, with no room for a rim and a floor inside it"
    ),
    "Maxwell Montes": (
        "the highest ground on the planet, and relief rather than albedo. Every "
        "marking on Venus is a flush colour inlay, so the globe's outer surface "
        "stays a true sphere; a raised massif would be the one thing on this "
        "world that breaks it"
    ),
    "the clouds": (
        "deliberately. The reference is the surface mapped through the "
        "atmosphere, and a cloud pattern and a radar map are two pictures of two "
        "different objects. The Mariner-10 ultraviolet cloud Y this revision "
        "deletes was the other one"
    ),
    "any terminator, limb shading or polar cap": (
        "the reference is a whole-globe mosaic assembled from many orbits and "
        "shows none of them"
    ),
}

#: ring name -> what this build coarsened and why.  Empty means the ring is
#: carried at the resolution it was drawn.
SIMPLIFIED: dict[str, str] = {
    "aphrodite_terra": (
        "built as two overlapping rings, `aphrodite_west` and `aphrodite_east`, "
        "rather than as one. Not a change to the feature: the two share 28 "
        "degrees of longitude, their union is the drawn ring exactly, and both "
        "cut chords lie inside that union where neither is a boundary of the "
        "highland. No vertex moved and no width changed. The reason is the "
        "outline construction's own limit -- `features/patches.py` refuses a "
        "ring reaching more than 72 degrees from its own mean axis, and "
        "Aphrodite as drawn reaches 77.23. The two halves reach 42.68 and "
        "48.45. Its narrowest neck is 1.184 mm either way, which is 2.96 nozzle "
        "widths, so no widening was needed"
    ),
}

#: Features carried in full that the finished piece cannot show, measured
#: rather than assumed.  `measure/venus-atlas-resolution.md` is the scan.
BURIED = {
    "ishtar_terra": (
        "drawn in full and invisible on the printed piece. Venus's 177.36 "
        "degree obliquity puts the planet's north pole at the bottom of the "
        "piece, and the globe is sunk 2.00 mm into its disc and carried by a "
        "seat cone springing at piece-latitude -42, so everything north of "
        "about Venusian +42 is inside the collar. Ishtar runs from +54 to +76 "
        "and lands entirely within it on both armies. It is not nothing in the "
        "solid, and that is measured rather than assumed: the part of it above "
        "the disc's own cut survives as a 3.04 mm3 body of `beige` spanning "
        "piece-latitude -49.29 to -41.89, which the shop will print and nobody "
        "will see -- its top edge clears the parallel where the collar springs "
        "by 0.11 degrees, 0.016 mm of arc. It is kept in the atlas because it "
        "is a real province of the supplied data and because the reason it "
        "cannot be seen is the inversion this revision is forbidden to "
        "correct -- not because anything about it is wrong"
    ),
    "atalanta_planitia": (
        "36 per cent of it is inside the collar for the same reason; the "
        "northern two thirds of the plain are visible"
    ),
}
