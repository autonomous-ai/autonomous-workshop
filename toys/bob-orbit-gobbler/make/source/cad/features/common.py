"""Robust profile helpers."""

import math
from build123d import Box, Cone, Cylinder, Polygon, Pos, Rot, Vector, extrude


def box_from(x: float, y: float, z: float, length: float, width: float, height: float):
    """Box placed by its minimum corner; build123d's Box is centre-aligned."""
    return Pos(x + length / 2.0, y + width / 2.0, z + height / 2.0) * Box(length, width, height)


def cylinder_from(radius: float, height: float, z: float = 0.0, x: float = 0.0, y: float = 0.0):
    """Cylinder placed from its bottom face; build123d's Cylinder is centre-aligned."""
    return Pos(x, y, z + height / 2.0) * Cylinder(radius, height)


def cylinder_x_from(radius: float, length: float, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    """X-axis cylinder placed by the minimum corner of its bounding box."""
    return Pos(x, y + radius, z + radius) * Rot(0.0, 90.0, 0.0) * cylinder_from(radius, length)


def cone_from(radius1: float, radius2: float, height: float, z: float = 0.0):
    """Conical frustum placed from its bottom face."""
    return Pos(0.0, 0.0, z + height / 2.0) * Cone(radius1, radius2, height)


def prism(points: list[tuple[float, float]], height: float):
    face = Polygon(*[Vector(x, y) for x, y in points])
    solid = extrude(face, amount=height)
    return Pos(0.0, 0.0, -solid.bounding_box().min.Z) * solid


def c_clip(outer_radius: float, inner_radius: float, thickness: float, opening: float):
    """Single-profile horseshoe clip with constant-width square-ended arms."""
    if not 0.0 < inner_radius < outer_radius or not 0.0 < opening < 2.0 * inner_radius:
        raise ValueError("invalid C-clip dimensions")
    steps = 36
    points = [(outer_radius, outer_radius), (0.0, outer_radius)]
    for i in range(1, steps + 1):
        angle = math.pi / 2.0 + math.pi * i / steps
        points.append((outer_radius * math.cos(angle), outer_radius * math.sin(angle)))
    points.extend([(outer_radius, -outer_radius), (outer_radius, -inner_radius), (0.0, -inner_radius)])
    for i in range(1, steps + 1):
        angle = -math.pi / 2.0 - math.pi * i / steps
        points.append((inner_radius * math.cos(angle), inner_radius * math.sin(angle)))
    points.append((outer_radius, inner_radius))
    return prism(points, thickness)


def ring_band(points_outer: list[tuple[float, float]], points_inner: list[tuple[float, float]], height: float):
    points = points_outer + list(reversed(points_inner))
    return prism(points, height)
