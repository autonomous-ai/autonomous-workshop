"""Moonwake Turn — one-piece dual-projection desk sculpture."""
import math

from build123d import Box, Cylinder, Location, Polygon, Vector, extrude, fillet

PRINTABLE = True

# Envelope and manufacturing parameters, millimetres. [assumed from Wish]
WIDTH = 94.0
DEPTH = 40.0
HEIGHT = 68.0
KEEL_HEIGHT = 12.0
MAST_WIDTH = 4.4


def xz_prism(points, depth=DEPTH):
    """Extrude a closed XZ polygon symmetrically through Y."""
    face = Polygon(*[Vector(x, 0, z) for x, z in points])
    return extrude(face, amount=depth / 2, both=True, dir=Vector(0, 1, 0))


def xy_prism(points, height=HEIGHT + 4):
    """Extrude a closed XY polygon vertically from just below the bed."""
    face = Polygon(*[Vector(x, y, -2) for x, y in points])
    return extrude(face, amount=height, dir=Vector(0, 0, 1))


def ship_silhouette():
    plate_depth = 4.4
    # Low rolling wave / keel: broad stable datum with an upturned bow.
    wave = xz_prism([
        (-47, 0), (47, 0), (47, 12), (42, 15), (36, 14), (29, 10),
        (18, 9), (7, 11), (-5, 13), (-17, 12), (-28, 10), (-39, 12), (-47, 12)
    ], depth=plate_depth)
    # Long pointed hull and one asymmetric sail avoid the tent-like double peak.
    hull = xz_prism([
        (-41, 12), (-39, 10), (42, 10), (43, 12), (41, 15),
        (35, 22), (33, 23), (-32, 23), (-34, 22), (-40, 15)
    ], depth=plate_depth)
    mast = Box(MAST_WIDTH, plate_depth, 48).moved(Location((-10, 0, 44)))
    # Give the long diagonal sail skin a 5 mm inward-biased depth so its
    # tessellated edge retains four-wall margin without changing the envelope.
    mainsail = xz_prism([(-7, 24), (-7, 60), (-4, 60), (29, 27), (29, 24)], depth=5.0)
    boom = xz_prism([(-10, 22), (32, 22), (32, 25), (-10, 25)], depth=plate_depth)
    pennant = xz_prism([(-9, 68), (8, 68), (8, 63), (-9, 63)], depth=plate_depth)
    cabin = xz_prism([(-31, 22), (-18, 22), (-18, 29), (-28, 29)], depth=plate_depth)
    profile = wave.fuse(hull, mast, boom, pennant, cabin)
    port = profile.moved(Location((0, -17.8, 0))).fuse(
        mainsail.moved(Location((0, -17.5, 0)))
    )
    starboard = profile.moved(Location((0, 17.8, 0))).fuse(
        mainsail.moved(Location((0, 17.5, 0)))
    )
    bed = Box(WIDTH, DEPTH, 4).moved(Location((0, 0, 2)))
    bed_top_edges = [
        edge
        for edge in bed.edges()
        if abs(edge.center().Z - 4) < 0.01
        and edge.bounding_box().size.X > 3
        and edge.bounding_box().size.Y < 0.01
    ]
    perforated_bed = fillet(bed_top_edges, radius=0.8)
    return port.fuse(starboard, perforated_bed)


def whale_aperture():
    # A whale outline: rounded forehead, two narrow outward-splayed water jets,
    # long pectoral flipper, tapered peduncle, and broad flukes.
    points = [
        (3, 1), (4, 4), (8, 6),
        (8, 7), (21, 7),
        (28, 6), (32, 5), (37, 2), (40, 2),
        (46, 9.5), (45, 4), (41, 1),
        (41, -1), (45, -4), (46, -9.5), (40, -3),
        (37, -3), (32, -5), (28, -7), (25, -11), (21, -7),
        (15, -7), (8, -6), (4, -4), (3, -1),
    ]
    body = xy_prism(points)
    # A small clear gap above the blowhole makes the two sprays read as water,
    # while simple four-sided slots avoid fragile acute wall junctions.
    left_jet = xy_prism([(9.83, 7.76), (7.63, 13.56), (9.97, 14.44), (12.17, 8.64)])
    right_jet = xy_prism([(12.83, 8.64), (15.03, 14.44), (17.37, 13.56), (15.17, 7.76)])
    return body, left_jet, right_jet


def moon_aperture():
    outer = Cylinder(10.5, HEIGHT + 4).moved(Location((-28, 1, HEIGHT / 2)))
    inner = Cylinder(8.0, HEIGHT + 4).moved(Location((-24, 1, HEIGHT / 2)))
    return outer.cut(inner)


def gen_step():
    whale, left_jet, right_jet = whale_aperture()
    cut_result = ship_silhouette().cut(whale, left_jet, right_jet, moon_aperture())
    # A tail-tip cutter can leave a sub-cubic-millimetre wave curl shaving;
    # retain the intentional connected manufactured body only.
    solid = max(cut_result.solids(), key=lambda candidate: candidate.volume)
    # A single restrained edge language turns the laminated construction into
    # a finished holdable object without changing either exact projection.
    depth_edges = []
    for edge in solid.edges():
        bounds = edge.bounding_box().size
        center = edge.center()
        runs_in_depth = bounds.Y > 3 and bounds.X < 0.01 and bounds.Z < 0.01
        finishes_mast = center.Z >= 63
        if runs_in_depth and finishes_mast:
            depth_edges.append(edge)
    solid = fillet(depth_edges, radius=0.8)
    solid.label = "moonwake_single_body"
    if len(solid.solids()) != 1:
        raise ValueError(f"Moonwake must be exactly one solid, got {len(solid.solids())}")
    if solid.bounding_box().min.Z < -1e-6:
        raise ValueError("Print datum must remain at Z=0")
    return solid
