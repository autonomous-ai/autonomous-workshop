"""Final edge selection and bounded rear-chassis repairs."""

from __future__ import annotations

import math

from build123d import chamfer, fillet


def _polar(radius: float, angle_deg: float):
    angle = math.radians(angle_deg)
    return radius * math.cos(angle), radius * math.sin(angle)


def _nearest_vertical(shape, x: float, y: float, tolerance: float):
    edges = [
        edge
        for edge in shape.edges()
        if abs(edge.tangent_at(0.5).Z) > 0.99
        and math.hypot(edge.center().X - x, edge.center().Y - y) < tolerance
    ]
    return min(edges, key=lambda edge: math.hypot(edge.center().X - x, edge.center().Y - y)) if edges else None


def finish_rear(shape, *, field_d, guide_id, front_z, rear_z, root_angle, free_angle, slot_r):
    """Chamfer continuous rims and round three detent junctions."""
    endpoints = [_polar(field_d / 2.0, angle) for angle in (root_angle, free_angle)]

    def horizontal_rim_edges(value, radius):
        found = []
        for edge in shape.edges():
            bounds = edge.bounding_box()
            midpoint = edge.position_at(0.5)
            touches_endpoint = abs(radius - field_d / 2.0) < 0.01 and any(
                math.hypot(vertex.X - x, vertex.Y - y) < 0.5
                for vertex in edge.vertices()
                for x, y in endpoints
            )
            if (
                abs(bounds.min.Z - value) < 0.01
                and abs(bounds.max.Z - value) < 0.01
                and abs(math.hypot(midpoint.X, midpoint.Y) - radius) < 0.12
                and edge.length > 1.0
                and not touches_endpoint
            ):
                found.append(edge)
        return found

    guide_edges = horizontal_rim_edges(front_z, guide_id / 2.0)
    shape = chamfer([max(guide_edges, key=lambda edge: edge.length)], 0.2)
    shape = chamfer(horizontal_rim_edges(rear_z, field_d / 2.0), 0.2)
    for radius, angle, tolerance in (
        (field_d / 2.0, free_angle, 0.20),
        (slot_r, root_angle, 0.30),
        (field_d / 2.0, root_angle, 0.20),
    ):
        x, y = _polar(radius, angle)
        edge = _nearest_vertical(shape, x, y, tolerance)
        if edge is not None:
            shape = fillet([edge], 0.2)
    return shape
