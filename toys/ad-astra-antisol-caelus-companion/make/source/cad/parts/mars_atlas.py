"""Mars's classical albedo map, as closed lon/lat rings.

The sibling of `parts/atlas.py`, and it is here for the same reason that one
is.  Mars is the second of the two worlds in this set whose surface has
outlines a person recognises: Syrtis Major has been drawn by every telescope
owner since 1659 and it is a dark triangle, not a circle.  A union of round
blobs throws that recognition away, so Mars, like Earth, is drawn from
outlines.  Every other world here wears an albedo map, a cloud pattern or a
band system that really is a union of round patches, and those stay in the
markings table where they belong.

Longitudes are areographic east, in the same 0-360 convention as the blob
table these rings replace.  Where a ring crosses the prime meridian its
longitudes simply continue past 360 -- 352, 358, 366 -- because the outline
tool works in 3-D directions and knows no seam.  Latitudes are degrees north.

These are stylised silhouettes at the accuracy an eyepiece sketch has, not
spacecraft mapping.  That is the right level: the reference is a distant view,
and these are the features that survive being seen from one.  Nothing here is
a crater, a volcano or a canyon; see `NOT_DRAWN` below and the note in
`parts/markings.py`.

Mars's globe is 14.72 mm across against Earth's 16.70, so one degree of arc is
0.128 mm here and every outline is finer than Earth's was.  `SIMPLIFIED`
records which rings that forced this build to coarsen and by how much.
`measure/mars-atlas-resolution.md` is the measurement it is read from.
"""

from __future__ import annotations

# --------------------------------------------------------- the dark wedge ---
#: The one feature on this planet a person names by shape: a broad northern
#: base and a point running south-west, the triangle the eyepiece shows.
SYRTIS_MAJOR = [
    (63, 17), (70, 20), (78, 19), (83, 13), (80, 4), (76, -4),
    (72, -8), (68, -3), (65, 5),
]

# ------------------------------------------------------- northern darkness --
MARE_ACIDALIUM = [
    (318, 30), (328, 42), (342, 51), (356, 55), (370, 51), (377, 41),
    (374, 30), (362, 25), (348, 24), (332, 25),
]

# -------------------------------------------------- the equatorial streak ---
#: Deliberately a thin streak, and the ring most at risk on a globe this size.
#: Carried at the width it was drawn: measured on the sphere its narrowest
#: printable width is 0.85 mm, twice the nozzle, so it holds without being
#: widened and without becoming a different shape.
SINUS_SABAEUS = [
    (296, -4), (310, -3), (326, -4), (340, -6), (352, -8), (358, -12),
    (352, -16), (340, -14), (326, -12), (310, -11), (298, -12),
]

#: The dark patch off Sabaeus's eastern end.  Its south-west corner was lifted
#: one degree so the red channel between the two clears the nozzle; see
#: SIMPLIFIED.
SINUS_MERIDIANI = [
    (352, 2), (358, 5), (363, 1), (359, -4), (354, -5), (349, -2),
]

# --------------------------------------------------------- southern belt ----
MARE_ERYTHRAEUM = [
    (300, -22), (312, -19), (328, -20), (342, -25), (348, -34),
    (340, -42), (324, -44), (310, -40), (301, -32),
]

#: These three are drawn as rings that touch, and are meant to fuse into the
#: one dark belt the reference shows running along the southern mid-latitudes.
#: Separate rings are only how that belt is described.  Two of the three joins
#: as drawn left a thread of red narrower than the nozzle, so four vertices
#: were moved to close them; see SIMPLIFIED.  Every moved vertex ends up
#: buried inside a neighbouring ring, so the belt's own outline -- the thing
#: the eye reads -- does not move.
MARE_SIRENUM = [
    (140, -22), (155, -17), (172, -16), (192, -20), (194, -30),
    (176, -36), (158, -37), (143, -33),
]

MARE_CIMMERIUM = [
    (187, -18), (205, -14), (222, -13), (238, -16), (255, -22),
    (246, -33), (230, -38), (212, -37), (193, -31),
]

MARE_TYRRHENUM = [
    (250, -14), (265, -12), (280, -16), (284, -26), (272, -32),
    (251, -29),
]


# ------------------------------------------------------------ polar caps ----
#: Unchanged from the blob table these rings sit beside: a blob centred on a
#: pole IS a polar cap, and these are the right sizes.  Only the rim is
#: corrected.  23 degrees puts the northern rim at latitude 67, 21 degrees puts
#: the southern rim at latitude -69.
CAP_NORTH_ANGULAR_RADIUS = 23.0
CAP_SOUTH_ANGULAR_RADIUS = 21.0

CAP_NORTH_RIM_LAT = 90.0 - CAP_NORTH_ANGULAR_RADIUS
CAP_SOUTH_RIM_LAT = -90.0 + CAP_SOUTH_ANGULAR_RADIUS

#: Lobes unioned onto the cap so its edge is ragged.  Left bare a cap ends on
#: an exact circle of latitude and reads as a lid laid on the globe rather than
#: as ice -- the Earth run established that, and this is the same fix.  The
#: north cap is the larger and the more irregular of the two, as the reference
#: shows: six lobes against four, reaching further past the rim and by more
#: varied amounts.
#:
#: Every lobe straddles its rim -- two vertices outside it, two inside -- so it
#: fuses with the cap instead of floating off its edge, and none of them makes
#: the cap bigger in the sense that matters: the angular radius above is
#: untouched and the lobes only break the circle it ends on.  The deepest
#: northern lobe reaches 6 degrees past the rim, 0.77 mm, and the deepest
#: southern one 4 degrees, 0.51 mm.
CAP_NORTH_LOBES = (
    [(14, 66), (45, 63), (60, 70), (30, 73)],
    [(80, 65), (110, 61), (136, 66), (106, 72)],
    [(150, 68), (180, 64), (201, 69), (170, 73)],
    [(216, 64), (245, 62), (261, 68), (231, 72)],
    [(276, 67), (300, 63), (316, 69), (291, 73)],
    [(326, 66), (348, 61), (362, 67), (342, 72)],
)

CAP_SOUTH_LOBES = (
    [(20, -67), (55, -66), (70, -71), (35, -74)],
    [(110, -68), (140, -65), (156, -71), (126, -74)],
    [(200, -67), (230, -66), (246, -72), (216, -74)],
    [(290, -68), (320, -66), (331, -72), (301, -74)],
)


# ------------------------------------------------------------ ring groups ---
#: The albedo group, in the order the appendix lists it.
ALBEDO_RINGS = [
    SYRTIS_MAJOR,
    MARE_ACIDALIUM,
    SINUS_SABAEUS,
    SINUS_MERIDIANI,
    MARE_ERYTHRAEUM,
    MARE_SIRENUM,
    MARE_CIMMERIUM,
    MARE_TYRRHENUM,
]

#: The rim-breaking lobes, north then south, as one group for the `caps`
#: marking to union onto its two polar blobs.
CAP_LOBES = list(CAP_NORTH_LOBES) + list(CAP_SOUTH_LOBES)

ALBEDO_NAMES = [
    "syrtis_major", "mare_acidalium", "sinus_sabaeus", "sinus_meridiani",
    "mare_erythraeum", "mare_sirenum", "mare_cimmerium", "mare_tyrrhenum",
]

#: name -> ring, for the resolution report and for naming a ring in a message.
RINGS = {
    "syrtis_major": SYRTIS_MAJOR,
    "mare_acidalium": MARE_ACIDALIUM,
    "sinus_sabaeus": SINUS_SABAEUS,
    "sinus_meridiani": SINUS_MERIDIANI,
    "mare_erythraeum": MARE_ERYTHRAEUM,
    "mare_sirenum": MARE_SIRENUM,
    "mare_cimmerium": MARE_CIMMERIUM,
    "mare_tyrrhenum": MARE_TYRRHENUM,
}
RINGS.update(
    {"cap_north_lobe_%d" % (index + 1): lobe
     for index, lobe in enumerate(CAP_NORTH_LOBES)}
)
RINGS.update(
    {"cap_south_lobe_%d" % (index + 1): lobe
     for index, lobe in enumerate(CAP_SOUTH_LOBES)}
)

#: Pairs the atlas draws overlapping on purpose, so the red between them is not
#: a question anybody asked.  These are the three joins of the southern belt.
FUSED_PAIRS = {
    ("mare_sirenum", "mare_cimmerium"),
    ("mare_cimmerium", "mare_tyrrhenum"),
}

#: What this atlas leaves out, with the reason, listed so nobody has to notice
#: it.  The reference is a distant view and shows none of these; drawing them
#: would be drawing from knowledge rather than from the thing this correction
#: is matching.
NOT_DRAWN = {
    "craters": (
        "at this radius a crater reads as a print defect rather than as a "
        "crater, and the reference shows none.  This is the same judgement the "
        "markings table already records for Mercury"
    ),
    "Olympus Mons and the Tharsis volcanoes": (
        "relief rather than albedo, and flat in a distant view.  A raised cone "
        "would also be the one thing on this globe that breaks its outer "
        "sphere, which is what every marking here exists not to do"
    ),
    "Valles Marineris": (
        "drawn generously it is about 0.4 mm wide at this globe size, so it "
        "could not carry a colour boundary on both sides"
    ),
    "Hellas and the bright basins": (
        "a fourth filament, and Mars has exactly three here -- red, "
        "cocoa_brown and white"
    ),
    "the bright beige highlands": (
        "the same; the globe's own red IS the highlands on this piece"
    ),
    "the dark collars that ring the real caps in spring": (
        "not in the reference, and at this size a collar reads as a mistake in "
        "the cap rather than as seasonal ice"
    ),
}

#: ring name -> what this build coarsened and by how much, in degrees of arc
#: and in millimetres on this globe.  `measure/mars-atlas-resolution.md` is the
#: measurement this is read from.
SIMPLIFIED: dict[str, str] = {
    "mare_sirenum": (
        "eastern edge moved 4 degrees of longitude east, from (188, -20) and "
        "(190, -30) to (192, -20) and (194, -30): 0.48 mm on this globe.  As "
        "drawn, Sirenum and Cimmerium came no closer than 0.32 mm, a thread "
        "of red narrower than the 0.40 mm nozzle, where the appendix means "
        "the two to fuse into one belt.  With Cimmerium's western edge moved "
        "to meet it the two now overlap by 0.46 mm2 and bite 0.37 mm into one "
        "another.  Both moved vertices end up inside the other ring, so the "
        "belt's own outline does not move."
    ),
    "mare_cimmerium": (
        "western edge moved 3 degrees of longitude west, from (190, -18) and "
        "(196, -31) to (187, -18) and (193, -31), 0.37 mm; and the eastern "
        "vertex 5 degrees east, from (250, -22) to (255, -22), 0.60 mm.  The "
        "western move closes the Sirenum join above.  The eastern one closes "
        "the Tyrrhenum join, which as drawn left 0.34 mm of red between two "
        "rings the appendix means to fuse; with Tyrrhenum's south-western "
        "vertex moved to meet it the two overlap by 0.24 mm2 and bite 0.53 mm "
        "into one another.  The eastern vertex ends up inside Tyrrhenum and "
        "the western one inside Sirenum, so again the belt's outline is "
        "where it was drawn."
    ),
    "mare_tyrrhenum": (
        "south-western vertex moved 5 degrees of longitude west, from "
        "(256, -29) to (251, -29), 0.56 mm, closing the Cimmerium join "
        "described above.  It moves into the notch between the two rings, "
        "which is the part of the belt the appendix asks to be filled."
    ),
    "sinus_meridiani": (
        "south-western vertex lifted 1 degree of latitude, from (354, -6) to "
        "(354, -5), 0.13 mm.  As drawn, Meridiani and Sabaeus came no closer "
        "than 0.36 mm and the red channel between them was under the nozzle.  "
        "These two are not a fused pair -- the appendix draws them as two "
        "features with sea between -- so the channel was opened to 0.46 mm "
        "rather than closed.  One degree is the smallest move that clears the "
        "nozzle, and neither outline changes shape."
    ),
}

#: Rings the appendix drew that this build carries exactly as drawn, recorded
#: because the Wish asks specifically after the thinnest of them.
UNCHANGED_NOTE = (
    "carried vertex for vertex.  It is the thinnest feature "
    "on this globe and the one the Wish names as most at risk, so it was "
    "measured rather than assumed: its narrowest printable width is 0.85 mm, "
    "twice the 0.40 mm nozzle.  It was neither widened nor dropped, and it is "
    "not a blob."
)
