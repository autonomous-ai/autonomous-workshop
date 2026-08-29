"""Connected positive creature profiles for exact shadow projection."""

from build123d import Pos

from features.common import bar_between, capsule, fuse_all, sketch_disk, sketch_ellipse, sketch_polygon


def round_cap(x: float, y: float, height: float):
    return Pos(x, y, 0) * sketch_disk(2.0, height)


def flat_tip_cap(x: float, y: float, height: float):
    return Pos(x, y - 0.7, 0) * capsule((-1.0, 0), (1.0, 0), 2.4, height)


def rabbit(height: float):
    return fuse_all([
        Pos(-3, -5, 0) * sketch_ellipse(11, 10, height),
        Pos(7, 5, 0) * sketch_ellipse(7, 6, height),
        Pos(13, 3, 0) * sketch_ellipse(4, 3, height),
        Pos(-14, -4, 0) * sketch_disk(4, height),
        capsule((3, 9), (0, 21), 4.8, height),
        capsule((8, 9), (8, 21), 4.5, height),
        bar_between((-9, -13), (-9, -25.5), 3.6, height),
        bar_between((4, -13), (4, -25.5), 3.6, height),
    ])


def fox(height: float):
    return fuse_all([
        Pos(2, -6, 0) * sketch_ellipse(12, 7, height),
        capsule((-6, -3), (-10, 4), 7, height),
        sketch_polygon([(-20, 4), (-16, 1), (-7, 2), (-3, 7), (-8, 11), (-15, 7)], height),
        sketch_polygon([(-12, 9), (-10, 20), (-6, 10)], height),
        sketch_polygon([(-7, 10), (-3, 18), (-2, 7)], height),
        sketch_polygon([(7, 1), (10, -7), (18, -4), (21, 3), (17, 12), (11, 8)], height),
        *[round_cap(x, y, height) for x, y in (
            (-20, 4), (-12, 9), (-2, 7), (17, 12), (21, 3),
        )],
        flat_tip_cap(-10, 20, height),
        flat_tip_cap(-3, 18, height),
        bar_between((-3, -11), (-3, -25.5), 3.8, height),
        bar_between((7, -11), (7, -25.5), 3.8, height),
    ])


def owl(height: float):
    head = sketch_polygon([
        (-12, 6), (-12, 12), (-9, 20), (-4, 15), (0, 18),
        (4, 15), (9, 20), (12, 12), (12, 6),
        (5, 3), (0, -1), (-5, 3),
    ], height)
    return fuse_all([
        head,
        # The torso meets the head only at the broad central beak/neck.  Wings
        # sit distinctly lower, creating exterior light notches at both
        # shoulders instead of the prior butterfly-like side cuts.
        Pos(0, -7, 0) * sketch_ellipse(7.5, 8.0, height),
        Pos(-10.5, -8, 0) * sketch_ellipse(4.5, 8.5, height),
        Pos(10.5, -8, 0) * sketch_ellipse(4.5, 8.5, height),
        capsule((-22, -20.5), (22, -20.5), 3.6, height),
        bar_between((-4.5, -14), (-4.5, -20.5), 4.0, height),
        bar_between((4.5, -14), (4.5, -20.5), 4.0, height),
        bar_between((0, -20.5), (0, -25.5), 4.0, height),
        flat_tip_cap(-9, 20, height),
        flat_tip_cap(9, 20, height),
        *[round_cap(x, y, height) for x, y in (
            (0, -1), (-6.5, -14), (6.5, -14),
        )],
    ])
