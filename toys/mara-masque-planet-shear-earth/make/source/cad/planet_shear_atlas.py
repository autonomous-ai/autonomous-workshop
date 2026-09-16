"""Stylised lon/lat outlines for the Planet Shear globe.

Outlines are deliberately chunky.  On a 21.08 mm globe one degree of arc is
0.184 mm, and a south-facing relief edge has to ramp about seven degrees to
print without support, so a landmass narrower than roughly fourteen degrees
loses its whole upper face to the ramp.  Every outline here is therefore a
simplified silhouette drawn to that floor -- Central America is one broad land
bridge rather than a thread, and the Indonesian arc is left to the sea -- and
follows the continents visible in the sealed reference image rather than a map.

Longitudes are true; `LON_OFFSET` in the parameter block turns the globe so the
Atlantic face -- Americas left, Africa and Europe right -- meets the viewer, the
way the reference is composed.
"""

NORTH_AMERICA = [
    (-168, 65), (-160, 71), (-140, 70), (-122, 70), (-100, 68), (-82, 73),
    (-62, 58), (-58, 48), (-68, 44), (-76, 36), (-82, 26), (-89, 20),
    (-97, 15), (-107, 20), (-116, 29), (-124, 40), (-126, 50), (-136, 58),
    (-152, 60),
]

# The land bridge, drawn as one mass wide enough to keep its upper face.
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

# Outlines never cross the +/-180 seam: a ring that did would be read as a band
# sweeping the long way round the globe.
# The cap over the pole itself has no lon/lat ring; it is built from its
# boundary latitude instead (see `polar_cap_cone`).  The lobes below carry the
# ice down onto the northern coasts and break up the rim, so the cap reads as an
# ice field rather than a disc laid on the globe.
ARCTIC_CAP_LAT = 72.0

# Enough lobes that the ice reaches a different latitude at nearly every
# longitude. Left as the bare cap, the rim is an exact circle of latitude, which
# in a front elevation is a straight line across the top of the globe and reads
# as a lid laid on it. Unions are the safe way to break that rim: leaning the cap
# cone instead left slivers where it grazed a lobe, and the printed body came out
# with open edges.
ARCTIC_LOBES = (
    [(-125, 66), (-95, 70), (-62, 71), (-72, 80), (-115, 78)],
    [(58, 68), (100, 70), (142, 67), (152, 77), (92, 80)],
    [(-5, 73), (38, 71), (52, 80), (8, 83)],
    [(150, 66), (176, 64), (172, 76), (146, 78)],
    [(-178, 66), (-152, 63), (-140, 72), (-176, 77)],
    [(20, 70), (56, 69), (60, 78), (24, 80)],
    [(-62, 68), (-30, 67), (-26, 76), (-58, 78)],
)

# Landmasses grouped by the body they fuse into, because each group becomes one
# addressable production solid and carries that name to the shop.
LANDMASS_GROUPS = (
    ("land_americas", (NORTH_AMERICA, CENTRAL_AMERICA, SOUTH_AMERICA)),
    ("land_africa", (AFRICA,)),
    ("land_eurasia", (EUROPE, ASIA)),
    ("land_australia", (AUSTRALIA,)),
)

LANDMASSES = tuple(o for _name, group in LANDMASS_GROUPS for o in group)

ICEFIELDS = (GREENLAND,) + ARCTIC_LOBES

SAHARA = [
    (-8, 18), (0, 25), (12, 27), (25, 26), (33, 27), (40, 20), (48, 14),
    (44, 8), (34, 12), (22, 14), (10, 13), (0, 12), (-6, 13),
]

KALAHARI = [(14, -19), (14, -28), (23, -26), (25, -19)]

INNER_ASIA = [(60, 38), (62, 46), (80, 48), (100, 46), (105, 40), (95, 36), (75, 35)]

AMERICAN_SOUTHWEST = [(-118, 30), (-114, 38), (-106, 38), (-100, 32), (-104, 26), (-112, 25)]

OUTBACK = [(119, -20), (118, -30), (128, -29), (140, -30), (145, -24), (140, -19), (128, -18)]

DRYLAND_GROUPS = (
    ("dryland_sahara", (SAHARA,)),
    ("dryland_kalahari", (KALAHARI,)),
    ("dryland_inner_asia", (INNER_ASIA,)),
    ("dryland_american_southwest", (AMERICAN_SOUTHWEST,)),
    ("dryland_outback", (OUTBACK,)),
)

DRYLANDS = tuple(o for _name, group in DRYLAND_GROUPS for o in group)
