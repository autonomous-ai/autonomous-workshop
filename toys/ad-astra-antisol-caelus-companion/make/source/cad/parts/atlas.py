"""Earth's coastlines, as closed lon/lat rings.

Six of the eight worlds in this set wear an albedo map, a cloud pattern or a
band system, and a union of round blobs is what those actually are.  Earth and
Mars are the two whose real surfaces have shapes a player already recognises,
so those two alone are drawn from outlines: Earth from the coastlines here,
Mars from the classical albedo map in `parts/mars_atlas.py`.  Nothing below
changed when Mars joined it -- Earth's rings, its filaments and its
subtractions are as they were.

Each ring is a closed loop of (longitude, latitude) in degrees, listed
counter-clockwise, and none crosses the +/-180 seam.  The outlines are
deliberately chunky silhouettes rather than survey coastlines: Central America
is one broad land bridge rather than a thread, and the Indonesian arc is left
to the sea.  Longitudes are true, so the Atlantic face of the printed globe is
the Atlantic face of the planet.

The rings are carried verbatim from the atlas supplied with this revision,
which was built and printed at globe scale on another toy.  `SIMPLIFIED`
records, for the record the Wish asks for, which of them this build had to
coarsen for a 16.70 mm globe and a 0.4 mm nozzle.
"""

from __future__ import annotations

NORTH_AMERICA = [
    (-168, 65), (-160, 71), (-140, 70), (-122, 70), (-100, 68), (-82, 73),
    (-62, 58), (-58, 48), (-68, 44), (-76, 36), (-82, 26), (-89, 20),
    (-97, 15), (-107, 20), (-116, 29), (-124, 40), (-126, 50), (-136, 58),
    (-152, 60),
]

CENTRAL_AMERICA = [
    (-103, 19), (-92, 11), (-80, 6), (-70, 8), (-70, 20), (-84, 25), (-97, 28),
]

SOUTH_AMERICA = [
    (-80, 8), (-74, 11), (-66, 11), (-58, 8), (-50, 2), (-44, -2), (-35, -6),
    (-38, -14), (-46, -24), (-54, -34), (-62, -44), (-72, -44), (-73, -32),
    (-70, -22), (-76, -14), (-81, -5), (-79, 2),
]

AFRICA = [
    (-17, 14), (-9, 22), (0, 32), (11, 37), (20, 32), (32, 31), (36, 22),
    (43, 12), (51, 12), (48, 2), (41, -5), (40, -16), (33, -25), (24, -34),
    (16, -32), (11, -16), (9, -1), (1, 5), (-8, 5),
]

EUROPE = [
    (-10, 36), (-9, 44), (-2, 48), (-5, 58), (8, 63), (18, 69), (30, 71),
    (44, 68), (58, 62), (60, 52), (50, 45), (40, 42), (28, 42), (20, 40),
    (12, 45), (4, 43), (-2, 39),
]

ASIA = [
    (38, 45), (44, 60), (58, 70), (75, 76), (100, 77), (120, 74), (140, 72),
    (162, 69), (170, 63), (158, 58), (140, 52), (136, 44), (126, 40),
    (122, 30), (112, 22), (104, 12), (100, 14), (94, 21), (88, 22), (80, 15),
    (77, 8), (72, 16), (66, 24), (58, 28), (48, 30), (40, 36),
]

AUSTRALIA = [
    (113, -22), (114, -34), (129, -32), (140, -38), (150, -37), (153, -27),
    (146, -17), (137, -12), (130, -12), (124, -16), (117, -20),
]

GREENLAND = [
    (-72, 78), (-55, 82), (-30, 83), (-20, 76), (-28, 68), (-42, 60),
    (-53, 62), (-62, 68),
]

ARCTIC_CAP_LAT = 72.0

ARCTIC_LOBES = (
    [(-125, 66), (-95, 70), (-62, 71), (-72, 80), (-115, 78)],
    [(58, 68), (100, 70), (142, 67), (152, 77), (92, 80)],
    [(-5, 73), (38, 71), (52, 80), (8, 83)],
    [(150, 66), (176, 64), (172, 76), (146, 78)],
    [(-178, 66), (-152, 63), (-140, 72), (-176, 77)],
    [(20, 70), (56, 69), (60, 78), (24, 80)],
    [(-62, 68), (-30, 67), (-26, 76), (-58, 78)],
)

SAHARA = [
    (-8, 18), (0, 25), (12, 27), (25, 26), (33, 27), (40, 20), (48, 14),
    (44, 8), (34, 12), (22, 14), (10, 13), (0, 12), (-6, 13),
]

KALAHARI = [(14, -19), (14, -28), (23, -26), (25, -19)]

INNER_ASIA = [(60, 38), (62, 46), (80, 48), (100, 46), (105, 40), (95, 36), (75, 35)]

AMERICAN_SOUTHWEST = [(-118, 30), (-114, 38), (-106, 38), (-100, 32), (-104, 26), (-112, 25)]

# (119, -20) in the supplied atlas.  Moved 2.24 degrees of arc -- 0.33 mm
# here -- east and south, the one simplification this globe size forced:
# see SIMPLIFIED below and `measure/earth-atlas-resolution.md`.
OUTBACK = [(121, -21), (118, -30), (128, -29), (140, -30), (145, -24), (140, -19), (128, -18)]


# ------------------------------------------------------------ land groups ---
AMERICAS = (NORTH_AMERICA, CENTRAL_AMERICA, SOUTH_AMERICA)
EURASIA = (EUROPE, ASIA)

#: name -> ring, for the resolution report and for naming a ring in a message.
RINGS = {
    "north_america": NORTH_AMERICA,
    "central_america": CENTRAL_AMERICA,
    "south_america": SOUTH_AMERICA,
    "africa": AFRICA,
    "europe": EUROPE,
    "asia": ASIA,
    "australia": AUSTRALIA,
    "greenland": GREENLAND,
    "sahara": SAHARA,
    "kalahari": KALAHARI,
    "inner_asia": INNER_ASIA,
    "american_southwest": AMERICAN_SOUTHWEST,
    "outback": OUTBACK,
}
RINGS.update(
    {"arctic_lobe_%d" % (index + 1): lobe for index, lobe in enumerate(ARCTIC_LOBES)}
)

LAND_RINGS = list(AMERICAS) + [AFRICA] + list(EURASIA) + [AUSTRALIA]
DRYLAND_RINGS = [SAHARA, KALAHARI, INNER_ASIA, AMERICAN_SOUTHWEST, OUTBACK]
ICE_RINGS = list(ARCTIC_LOBES) + [GREENLAND]

#: What the supplied atlas leaves out, with the reason, listed so nobody has
#: to notice it.  These are omissions of the source data rather than
#: simplifications this build made -- the atlas was drawn as a chunky
#: silhouette -- but they are the set's omissions now, so they are stated.
NOT_DRAWN = {
    "Japan": (
        "about 2.6 mm long and 0.3 mm wide at this globe size, so its width is "
        "under the 0.4 mm nozzle and it could not carry a colour boundary on "
        "both sides"
    ),
    "New Zealand": "the same, and smaller",
    "the Indonesian and Philippine arcs": (
        "a chain of islands each well under the nozzle; the atlas leaves the "
        "arc to the sea by design"
    ),
    "the British Isles as a shape of their own": (
        "inside Europe's ring rather than separate from it; the Channel is "
        "0.2 mm here"
    ),
    "the Mediterranean's islands": "all under the nozzle",
    "Antarctica, and with it any southern ice": (
        "not in the supplied atlas at all. The globe is also cut off where it "
        "sinks into its disc, which at this obliquity removes everything south "
        "of about 73 degrees on the longitude facing the lean and about 26 "
        "degrees on the longitude opposite it, so a southern cap would be part "
        "hidden in any case"
    ),
}

#: ring name -> what this build coarsened and by how much, in degrees of arc.
#: Empty means every ring above is carried at the resolution it was drawn.
#: `measure/earth-atlas-resolution.md` is the measurement this is read from.
SIMPLIFIED: dict[str, str] = {
    "outback": (
        "north-west corner moved from (119, -20) to (121, -21), 2.24 degrees "
        "of arc and 0.33 mm on this globe.  As drawn it ran 0.14 mm inside "
        "Australia's west coast, leaving 1.17 mm of green strip thinner than "
        "the 0.4 mm nozzle could print; moved, the narrowest green anywhere "
        "along it is 0.40 mm.  The outback is an interior beige patch, so the "
        "silhouette a player recognises -- Australia's own coastline -- does "
        "not move at all."
    ),
}
