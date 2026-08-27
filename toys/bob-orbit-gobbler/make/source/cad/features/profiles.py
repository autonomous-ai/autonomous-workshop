"""Cam and mouth profile helpers."""

import math
from build123d import fillet
import params as p
from features.common import ring_band


def variable_cam_wall(inner: bool):
    """Build a constant-thickness wall by offsetting the cam along true normals."""
    centerline = []
    for i in range(p.CAM_SAMPLES):
        # Half-step the closed profile so its unavoidable polygon seam does
        # not coincide with the Cartesian symmetry axis and create duplicate
        # collinear mesh edges at x=0.
        a = 360.0 * (i + 0.5) / p.CAM_SAMPLES
        centerline.append(p.polar_xy(p.cam_radius(a), a))
    side_a = []
    side_b = []
    if inner:
        offsets = (-(p.CAM_GROOVE_W / 2.0 + p.CAM_WALL), -p.CAM_GROOVE_W / 2.0)
    else:
        offsets = (p.CAM_GROOVE_W / 2.0, p.CAM_GROOVE_W / 2.0 + p.CAM_WALL)
    for i, (x, y) in enumerate(centerline):
        x0, y0 = centerline[(i - 1) % p.CAM_SAMPLES]
        x1, y1 = centerline[(i + 1) % p.CAM_SAMPLES]
        tx, ty = x1 - x0, y1 - y0
        length = math.hypot(tx, ty)
        nx, ny = -ty / length, tx / length
        if inner:
            nx, ny = -nx, -ny
        side_a.append((x + nx * abs(offsets[0]), y + ny * abs(offsets[0])))
        side_b.append((x + nx * abs(offsets[1]), y + ny * abs(offsets[1])))
    wall = ring_band(side_a, side_b, p.CAM_HEIGHT)
    seam_edges = [
        edge
        for edge in wall.edges()
        if abs(edge.length - p.CAM_HEIGHT) < 0.01
        and abs(edge.center().X) < 1.5
        and edge.center().Y > 45.0
    ]
    return fillet(seam_edges, radius=0.4)


def polar_sector(r_inner: float, r_outer: float, a0: float, a1: float, height: float, samples: int = 24):
    outer = [p.polar_xy(r_outer, a0 + (a1 - a0) * i / samples) for i in range(samples + 1)]
    inner = [p.polar_xy(r_inner, a0 + (a1 - a0) * i / samples) for i in range(samples + 1)]
    return ring_band(outer, inner, height)
