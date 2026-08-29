"""Parametric one-piece Comet Pebble, authored in its support-free print stance."""

import math

from build123d import (
    Align,
    Box,
    CenterOf,
    Cylinder,
    Edge,
    Face,
    Plane,
    Pos,
    Solid,
    Wire,
)

PRINTABLE = True

# [selected Inventor] Skew-keel rattleback stations; final tuple is rotation deg.
BODY_STATIONS = (
    # z, x radius, y radius, x center, y center, ellipse angle
    (-1.0, 18.0, 11.0, 0.0, 0.0, 0.0),
    (1.6, 18.0, 11.0, 0.0, 0.0, 0.0),
    (4.6, 21.0, 14.0, 0.0, -0.2, 10.0),
    (10.6, 27.0, 20.0, 0.4, -0.7, 10.0),
    (17.6, 34.0, 22.0, 0.8, -0.8, -2.0),
    (22.0, 27.0, 17.0, 1.2, -0.3, -10.0),
    (28.0, 18.0, 11.0, -0.5, 0.8, -14.0),
    (32.0, 8.0, 4.5, -1.5, 1.2, -17.0),
    (33.2, 4.2, 3.2, -3.8, 2.8, -17.0),
    (34.0, 4.2, 3.2, -3.8, 2.8, -17.0),
)
STAR_OUTER_RADIUS = 7.0
STAR_INNER_RADIUS = 3.8
STAR_CORNER_RADIUS = 0.80
STAR_BASE_Z = 30.50
STAR_HEIGHT = 0.90
FACE_POST_RADIUS = 0.80
FACE_POST_TOP_Z = 33.00
CROWN_EDGE_FILLET = 0.80
SOLE_EDGE_FILLET = 0.80


def _ellipse_wire(z, rx, ry, cx, cy, angle_degrees):
    angle = math.radians(angle_degrees)
    x_direction = (math.cos(angle), math.sin(angle), 0)
    plane = Plane(origin=(cx, cy, z), x_dir=x_direction, z_dir=(0, 0, 1))
    return Wire([Edge.make_ellipse(rx, ry, plane)])


def _rounded_star_wire(z):
    points = []
    for index in range(10):
        angle = math.pi / 2 + index * math.pi / 5
        radius = STAR_OUTER_RADIUS if index % 2 == 0 else STAR_INNER_RADIUS
        points.append((radius * math.cos(angle), radius * math.sin(angle), z))
    raw = Wire.make_polygon(points, close=True)
    return raw.fillet_2d(STAR_CORNER_RADIUS, raw.vertices())


def _face_posts():
    eye_and_smile = (
        (-2.2, 1.0),
        (2.2, 1.0),
        (-3.2, -1.3),
        (-2.2, -2.2),
        (-1.1, -2.8),
        (1.1, -2.8),
        (2.2, -2.2),
        (3.2, -1.3),
    )
    posts = None
    for x_coord, y_coord in eye_and_smile:
        post = Pos(x_coord, y_coord, 30.0) * Cylinder(
            FACE_POST_RADIUS,
            FACE_POST_TOP_Z - 30.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        posts = post if posts is None else posts.fuse(post)
    return posts


def _star_relief():
    return Solid.extrude(
        Face(_rounded_star_wire(STAR_BASE_Z)),
        (0, 0, STAR_HEIGHT),
    )


def gen_step():
    station_wires = [_ellipse_wire(*station) for station in BODY_STATIONS]
    body = Solid.make_loft(station_wires, ruled=False)
    horizontal_edges = [
        edge for edge in body.edges() if edge.bounding_box().size.Z < 1e-4
    ]
    crown_edge = max(horizontal_edges, key=lambda edge: edge.bounding_box().min.Z)
    body = body.fillet(CROWN_EDGE_FILLET, [crown_edge])
    below_bed = Box(
        200.0,
        200.0,
        100.0,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    printable_body = body.cut(below_bed)
    sole_edge = min(
        [
            edge
            for edge in printable_body.edges()
            if edge.bounding_box().size.Z < 1e-4
        ],
        key=lambda edge: edge.bounding_box().min.Z,
    )
    printable_body = printable_body.fillet(SOLE_EDGE_FILLET, [sole_edge])
    pebble = printable_body.fuse(_star_relief(), _face_posts())
    pebble.label = "comet_pebble_one_piece"

    assert pebble.is_valid
    assert len(pebble.solids()) == 1
    assert abs(pebble.bounding_box().min.Z) < 1e-6
    center = pebble.center(CenterOf.MASS)
    assert (center.X / BODY_STATIONS[0][1]) ** 2 + (
        center.Y / BODY_STATIONS[0][2]
    ) ** 2 < 1.0
    return pebble
