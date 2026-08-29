"""Stable low-level feature builders."""

from __future__ import annotations

import math

from build123d import Box, Cylinder, Face, GeomType, Location, SlotOverall, Solid, Vector, Wire, Align


def annulus(outer_radius: float, inner_radius: float, height: float):
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    return Cylinder(outer_radius, height, align=alignment) - Cylinder(inner_radius, height + 0.2, align=alignment)


def polar_sector(inner_radius: float, outer_radius: float, start_deg: float, span_deg: float, height: float):
    if not 0.0 < span_deg < 180.0:
        raise ValueError("polar_sector supports spans between 0 and 180 degrees")
    if inner_radius <= 0.0:
        ring = Cylinder(outer_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    else:
        ring = annulus(outer_radius, inner_radius, height)
    far = outer_radius * 4.0
    angles = (start_deg, start_deg + span_deg / 2.0, start_deg + span_deg)
    points = [Vector(0, 0, 0)]
    points.extend(
        Vector(far * math.cos(math.radians(angle)), far * math.sin(math.radians(angle)), 0)
        for angle in angles
    )
    wedge = Solid.extrude(Face(Wire.make_polygon(points, close=True)), Vector(0, 0, height))
    return ring & wedge


def radial_box(radial_length: float, tangential_width: float, height: float, center_radius: float, angle_deg: float, z: float):
    box = Box(radial_length, tangential_width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    placed = Location((center_radius, 0, z)) * box
    return Location((0, 0, 0), (0, 0, angle_deg)) * placed


def rounded_radial_box(radial_length: float, tangential_width: float, height: float, corner_radius: float, center_radius: float, angle_deg: float, z: float, *, round_ends: bool = True):
    """Radial prism with an exact rounded-rectangle YZ section."""
    x_center = center_radius
    shape = Location((x_center, 0, z)) * Box(
        radial_length,
        tangential_width - 2.0 * corner_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    middle_height = height - 2.0 * corner_radius
    if middle_height > 1e-6:
        shape += Location((x_center, 0, z + corner_radius)) * Box(
            radial_length,
            tangential_width,
            middle_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        corner_positions = [
            (y_sign, z_sign)
            for y_sign in (-1.0, 1.0)
            for z_sign in (-1.0, 1.0)
        ]
    else:
        corner_positions = [(y_sign, 0.0) for y_sign in (-1.0, 1.0)]
    for y_sign, z_sign in corner_positions:
        corner = Cylinder(
            corner_radius,
            radial_length,
            rotation=(0, 90, 0),
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        corner_y = y_sign * (tangential_width / 2.0 - corner_radius)
        corner_z = z + height / 2.0 + z_sign * max(height / 2.0 - corner_radius, 0.0)
        shape += Location((x_center, corner_y, corner_z)) * corner
    if round_ends:
        shape = shape.fillet(corner_radius, shape.edges())
    return Location((0, 0, 0), (0, 0, angle_deg)) * shape


def half_annulus(radius_outer: float, radius_inner: float, height: float, inward: bool = True):
    ring = annulus(radius_outer, radius_inner, height)
    width = radius_outer * 2.2
    clip_x = -radius_outer if inward else 0.0
    clip = Location((clip_x, -radius_outer * 1.1, 0)) * Box(
        radius_outer,
        width,
        height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    half = ring & clip
    return half.chamfer(0.8, None, half.edges())


def rib_bar(
    radial_inner: float,
    radial_outer: float,
    root_width: float,
    height: float,
    center_radius: float,
    angle_deg: float,
    crest_width: float,
    crest_radius: float,
):
    length = radial_outer - radial_inner
    ramp_run = (root_width - crest_width) / 2.0
    crest_length = length - 2.0 * ramp_run
    root_wire = SlotOverall(length, root_width).wire()
    crest_wire = Location((0, 0, height)) * SlotOverall(crest_length, crest_width).wire()
    rib = Solid.make_loft([root_wire, crest_wire])
    crest_edges = [
        edge
        for edge in rib.edges()
        if abs(edge.center().Z - height) < 1e-6 and edge.geom_type == GeomType.LINE
    ]
    rib = rib.fillet(crest_radius, crest_edges)
    placed = Location((center_radius, 0, 0)) * rib
    return Location((0, 0, 0), (0, 0, angle_deg)) * placed
