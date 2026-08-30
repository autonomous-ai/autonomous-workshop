"""Starling Gate — one-piece rocking silhouette toy, dimensions in millimetres."""

from math import cos, pi, sin

from build123d import BuildPart, BuildSketch, Mode, Plane, Polygon, extrude

PRINTABLE = True

WIDTH = 82.0
HEIGHT = 96.0
THICKNESS = 18.0


def _outer_points():
    # Convex rocker belly: lowest at centre, 4.0 mm rise at the shoulders.
    pts = []
    for i in range(25):
        x = -41.0 + 82.0 * i / 24
        pts.append((x, 4.0 * (x / 41.0) ** 2))
    pts.extend([(41.0, 56.0)])
    # A tall, iconic pointed arch.
    for i in range(17):
        a = i * pi / 16
        pts.append((41.0 * cos(a), 56.0 + 40.0 * sin(a)))
    pts.append((-41.0, 56.0))
    return pts


def _bird_void_points():
    # Single negative-space glyph: perched bird upright. During a rock the long
    # swept tail becomes a shooting-star trail and the beak becomes its point.
    return [
        (-27.0, 32.0), (-12.0, 49.0), (1.0, 63.0), (13.0, 68.0),
        (25.0, 62.0), (12.0, 51.0), (2.0, 30.0),
    ]


def _star_points(cx=22.0, cy=77.0, r_outer=5.5, r_inner=2.5):
    pts = []
    for i in range(10):
        angle = pi / 2 + i * pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * cos(angle), cy + r * sin(angle)))
    return pts


def gen_step():
    with BuildPart() as model:
        with BuildSketch(Plane.XY) as outline:
            Polygon(*_outer_points())
            Polygon(*_bird_void_points(), mode=Mode.SUBTRACT)
            Polygon(*_star_points(), mode=Mode.SUBTRACT)
        extrude(amount=THICKNESS)
    return model.part
