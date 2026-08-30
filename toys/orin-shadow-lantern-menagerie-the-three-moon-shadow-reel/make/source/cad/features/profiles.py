"""Connected positive creature profiles for exact shadow projection."""

from build123d import Axis, Pos, fillet

from features.common import bar_between, capsule, fuse_all, sketch_disk, sketch_ellipse, sketch_polygon


def round_cap(x: float, y: float, height: float):
    return Pos(x, y, 0) * sketch_disk(2.0, height)


def rounded_polygon(points: list[tuple[float, float]], height: float):
    """Round planar polygon corners without adding an external bulb or flat cap."""
    prism = sketch_polygon(points, height)
    return fillet(prism.edges().filter_by(Axis.Z), radius=0.8)


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
        # A long low forehead, pointed muzzle, and two compact triangular ears
        # replace the prior capped stalks that read as antlers or antennae.
        rounded_polygon([(-21, 3.5), (-16, 0.5), (-7, 2), (-3, 7), (-7, 10), (-15, 7)], height),
        rounded_polygon([(-13, 8), (-11, 16), (-7, 9)], height),
        rounded_polygon([(-8, 9), (-5, 15), (-3, 7)], height),
        # High brush tip and a narrowed root make the tail distinct from the
        # torso even after the portal crop and point-source magnification.
        rounded_polygon([(7, 0), (10, -7), (16, -4), (19, 2), (16, 12), (10, 8)], height),
        bar_between((-3, -11), (-3, -25.5), 3.8, height),
        bar_between((7, -11), (7, -25.5), 3.8, height),
    ])


def owl(height: float):
    head = rounded_polygon([
        (-11, 5), (-11, 11), (-8, 17), (-4, 14), (0, 16),
        (4, 14), (8, 17), (11, 11), (11, 5),
        (5, 2), (0, -4), (-5, 2),
    ], height)
    return fuse_all([
        head,
        # The long external beak projects into two open shoulder notches.  A
        # pear body and tapered angular wings replace three round lower lobes,
        # which previously read as a bat, butterfly, or mask.
        Pos(0, -10, 0) * sketch_ellipse(7.5, 7.5, height),
        rounded_polygon([(-4, -5), (-9, -4), (-14, -9), (-12, -17), (-7, -18), (-5, -12)], height),
        rounded_polygon([(4, -5), (9, -4), (14, -9), (12, -17), (7, -18), (5, -12)], height),
        capsule((-22, -20.5), (22, -20.5), 3.6, height),
        bar_between((-4.5, -15), (-4.5, -20.5), 4.0, height),
        bar_between((4.5, -15), (4.5, -20.5), 4.0, height),
        bar_between((0, -20.5), (0, -25.5), 4.0, height),
    ])
