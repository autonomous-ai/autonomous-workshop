"""Shadow reel builder."""

import math

from build123d import Align, Cone, Cylinder, Pos, Rot

from features.common import bar_between, fuse_all, sketch_disk, sketch_polygon
from features.profiles import fox, owl, rabbit
from params import *


def make_shadow_reel():
    outer_points = []
    for index in range(PLANAR_CURVE_FACETS):
        angle = 2 * math.pi * index / PLANAR_CURVE_FACETS
        radius = 56.6 + 0.4 * math.cos(12 * angle)
        outer_points.append((math.cos(angle) * radius, math.sin(angle) * radius))
    outer = sketch_polygon(outer_points, REEL_T)
    inner = sketch_disk(REEL_RING_INNER_R, REEL_T + 1.0)
    ring = outer.cut(Pos(0, 0, -0.5) * inner)
    shapes = [ring, sketch_disk(REEL_HUB_R, REEL_T)]
    for angle in (30.0, 150.0, 270.0):
        rad = math.radians(angle)
        shapes.append(bar_between(
            (0.0, 0.0), (math.cos(rad) * 58.0, math.sin(rad) * 58.0),
            SPOKE_W, REEL_T,
        ))
    for angle in (-90.0, 30.0, 150.0):
        rad = math.radians(angle)
        shapes.append(Pos(math.cos(rad) * 52.5, math.sin(rad) * 52.5, 0) * sketch_disk(5.6, REEL_T))
    for animal, angle in ((rabbit(REEL_T), 0.0), (fox(REEL_T), 120.0), (owl(REEL_T), 240.0)):
        shapes.append(Rot(0, 0, angle) * (Pos(0, CREATURE_PITCH_R, 0) * animal))
    reel = fuse_all(shapes).intersect(outer).first
    bore = Pos(0, 0, -0.5) * Cylinder(
        SPINDLE_BORE_D / 2, REEL_T + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    reel = reel.cut(bore)
    for points in (
        [(57.2, -6.0), (56.2, -4.0), (57.2, -2.0)],
        [(57.2, 2.0), (56.2, 4.0), (57.2, 6.0)],
    ):
        reel = reel.cut(Pos(0, 0, -0.1) * sketch_polygon(points, REEL_T + 0.2))
    for angle, depth in (
        (-90.0, DETENT_POCKET_DEPTH_RABBIT),
        (30.0, DETENT_POCKET_DEPTH_OTHER),
        (150.0, DETENT_POCKET_DEPTH_OTHER),
    ):
        rad = math.radians(angle)
        x, y = math.cos(rad) * 52.5, math.sin(rad) * 52.5
        ramp = Pos(x, y, -0.1) * Cone(
            DETENT_POCKET_MOUTH_R, DETENT_POCKET_R,
            DETENT_POCKET_RAMP_DEPTH + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        core = Pos(x, y, DETENT_POCKET_RAMP_DEPTH) * Cylinder(
            DETENT_POCKET_R, depth - DETENT_POCKET_RAMP_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        reel = reel.cut(ramp.fuse(core))
    reel.label = "shadow_reel"
    assert len(reel.solids()) == 1
    return reel
