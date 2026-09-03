"""One-piece Pocket Eclipse Menagerie shadow caster.

Coordinate convention: Z up; owl light travels +X; rabbit light travels +Y.
The two broad silhouette slabs are united into one printable solid. Decorative
fox/crescent relief is shallow along X and remains inside the rabbit envelope.
"""
from math import cos, pi, sin

from build123d import Box, Face, Vector, Wire, extrude

PRINTABLE = True

SLAB = 4.0
RELIEF = 2.0


def _face_yz(points, rounded=True):
    face = Face(Wire.make_polygon([Vector(0, y, z) for y, z in points], close=True))
    return face.fillet_2d(0.65, face.vertices()) if rounded else face


def _face_xz(points):
    face = Face(Wire.make_polygon([Vector(x, 0, z) for x, z in points], close=True))
    return face.fillet_2d(0.65, face.vertices())


def _ellipse_yz(cy, cz, ry, rz, n=64):
    return [(cy + ry * cos(2 * pi * i / n), cz + rz * sin(2 * pi * i / n)) for i in range(n)]


def _owl_slab():
    # Frontal owl: paired ear tufts, broad head, swept wings, body and talons.
    outline = [
        (-12, 0), (-16, 3), (-20, 10), (-25, 18), (-28, 30),
        (-23, 39), (-20, 52), (-25, 66), (-23, 69), (-13, 63),
        (-8, 74), (-5, 76), (-2, 74), (0, 66),
        (2, 74), (5, 76), (8, 74), (13, 63), (23, 69), (25, 66), (20, 52),
        (23, 39), (28, 30), (25, 18), (20, 10), (16, 3),
        (12, 0),
    ]
    return extrude(_face_yz(outline), amount=SLAB, dir=Vector(1, 0, 0)).translate((-SLAB / 2, 0, 0))


def _rabbit_slab():
    # Side-on airborne rabbit: long rear legs/tail at left, arched body,
    # forward paws and muzzle at right, with two swept ears above.
    outline = [
        (-37, 0), (-42, 4), (-46, 6), (-47, 9), (-44, 12), (-42, 13), (-34, 15),
        (-27, 26), (-19, 36), (-10, 42), (-4, 46),
        (-7, 58), (-6, 73), (-4, 76), (-1, 76), (0, 64),
        (3, 76), (5, 78), (7, 77), (8, 74), (6, 58),
        (12, 54), (18, 48), (25, 45), (31, 39), (37, 38), (40, 36), (38, 34),
        (34, 32), (27, 31), (33, 26), (42, 22), (39, 18),
        (29, 19), (22, 23), (15, 20), (8, 14), (1, 9),
        (-8, 5), (-18, 0),
    ]
    return extrude(_face_xz(outline), amount=SLAB, dir=Vector(0, 1, 0)).translate((0, -SLAB / 2, 0))


def _fox_relief():
    # A curled sleeping fox read from the +X face: oval body, tucked head,
    # pointed ears, and a broad tail crossing the body.
    body = extrude(_face_yz(_ellipse_yz(0, 25, 16, 13), rounded=False), amount=RELIEF, dir=Vector(1, 0, 0))
    head_pts = [(6, 32), (12, 39), (17, 37), (19, 31), (15, 27), (10, 28)]
    head = extrude(_face_yz(head_pts), amount=RELIEF, dir=Vector(1, 0, 0))
    ear_a = extrude(_face_yz([(10, 37), (11, 44), (14, 44), (16, 38)]), amount=RELIEF, dir=Vector(1, 0, 0))
    ear_b = extrude(_face_yz([(15, 37), (18, 42), (21, 41), (19, 35)]), amount=RELIEF, dir=Vector(1, 0, 0))
    tail_pts = [(-15, 23), (-8, 13), (3, 10), (13, 16), (16, 23),
                (11, 19), (3, 17), (-5, 19), (-10, 27)]
    tail = extrude(_face_yz(tail_pts), amount=RELIEF, dir=Vector(1, 0, 0))
    return (body + head + ear_a + ear_b + tail).translate((SLAB / 2, 0, 0))


def _crescent_relief():
    # A blunt crescent-like shelter made from three broad relief ribbons;
    # squared roots avoid tangent knife edges at the nozzle scale.
    left = [(-20, 27), (-16, 27), (-14, 49), (-8, 62), (-4, 65), (-7, 68), (-12, 64), (-18, 51)]
    crown = [(-7, 68), (-4, 65), (5, 64), (13, 58), (16, 60), (8, 69), (0, 72)]
    right = [(13, 58), (16, 60), (20, 50), (21, 37), (18, 31), (15, 33), (17, 43)]
    crescent = extrude(_face_yz(left), amount=RELIEF, dir=Vector(1, 0, 0))
    crescent += extrude(_face_yz(crown), amount=RELIEF, dir=Vector(1, 0, 0))
    crescent += extrude(_face_yz(right), amount=RELIEF, dir=Vector(1, 0, 0))
    return crescent.translate((SLAB / 2, 0, 0))


def gen_step():
    # The owl's high bifurcated crown is also the held crescent arch; the fox
    # relief remains shallow and entirely supported by the broad owl mask.
    crown_bridge = Box(8, 8, 6).translate((-4, -4, 69))
    shape = _owl_slab() + _rabbit_slab() + _fox_relief() + crown_bridge
    assert len(shape.solids()) == 1, "caster must remain one connected printed solid"
    return shape
