"""Parametric geometry and route math for the Eclipse Braid desk toy."""

from __future__ import annotations

import math
from dataclasses import dataclass

from build123d import (
    Box,
    Color,
    Compound,
    Cylinder,
    Edge,
    Face,
    Location,
    Plane,
    Solid,
    Vector,
    Wire,
)


@dataclass(frozen=True)
class BraidParameters:
    # All dimensions are millimetres. XY is the desk plane; +Z is up.
    half_straight: float = 34.0
    strand_offset: float = 11.0
    lobe_radius_x: float = 16.0
    low_rail_z: float = 10.4
    high_rail_z: float = 23.8
    crossing_x: float = 17.0
    bridge_half_span: float = 16.5
    rail_radius: float = 2.2
    web_thickness: float = 1.5
    base_thickness: float = 2.6
    base_rib_width: float = 6.0
    frame_outer_x: float = 58.0
    frame_outer_y: float = 42.0
    frame_width: float = 7.0
    runner_inner_radius: float = 3.4
    runner_outer_radius: float = 6.0
    runner_length: float = 3.6
    runner_slot_width: float = 2.4
    support_clear_radius: float = 7.2


P = BraidParameters()


def _bridge_bump(x: float, centre_x: float) -> float:
    """Compact C1 cosine bridge bump, exactly zero outside its span."""
    distance = abs(x - centre_x)
    if distance >= P.bridge_half_span:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * distance / P.bridge_half_span))


def route_points(samples_per_straight: int = 64, samples_per_lobe: int = 32):
    """Closed ordered centerline; endpoints are implicit through periodicity.

    The first strand bridges over at x=-crossing_x.  The return strand bridges
    over at x=+crossing_x, yielding two separated alternating crossings.
    """
    pts: list[tuple[float, float, float]] = []

    # Forward central strand: left upper port to right upper port.
    for i in range(samples_per_straight):
        s = i / samples_per_straight
        x = -P.half_straight + 2.0 * P.half_straight * s
        y = P.strand_offset * math.cos(2.0 * math.pi * s)
        z = P.low_rail_z + (P.high_rail_z - P.low_rail_z) * _bridge_bump(
            x, -P.crossing_x
        )
        pts.append((x, y, z))

    # Right half-ellipse, upper port to lower port.
    for i in range(samples_per_lobe):
        u = i / samples_per_lobe
        angle = math.pi * u
        pts.append(
            (
                P.half_straight + P.lobe_radius_x * math.sin(angle),
                P.strand_offset * math.cos(angle),
                P.low_rail_z,
            )
        )

    # Return central strand: right lower port to left lower port.
    for i in range(samples_per_straight):
        q = i / samples_per_straight
        x = P.half_straight - 2.0 * P.half_straight * q
        s = (x + P.half_straight) / (2.0 * P.half_straight)
        y = -P.strand_offset * math.cos(2.0 * math.pi * s)
        z = P.low_rail_z + (P.high_rail_z - P.low_rail_z) * _bridge_bump(
            x, P.crossing_x
        )
        pts.append((x, y, z))

    # Left half-ellipse, lower port back to upper port.
    for i in range(samples_per_lobe):
        u = i / samples_per_lobe
        angle = math.pi * u
        pts.append(
            (
                -P.half_straight - P.lobe_radius_x * math.sin(angle),
                -P.strand_offset * math.cos(angle),
                P.low_rail_z,
            )
        )
    return pts


def planar_route_points():
    return [(x, y, P.base_thickness / 2.0) for x, y, _ in route_points()]


def _periodic_spline(points):
    return Edge.make_spline([Vector(*point) for point in points], periodic=True)


def _circle_face(origin, normal, radius):
    normal_v = Vector(*normal).normalized()
    # Global Z remains the profile's stable vertical direction because no path
    # tangent is vertical. The orthogonal in-plane direction follows from it.
    x_dir = Vector(0, 0, 1).cross(normal_v).normalized()
    plane = Plane(origin=Vector(*origin), x_dir=x_dir, z_dir=normal_v)
    return Face(Wire.make_circle(radius, plane=plane))


def make_rail():
    pts = route_points()
    # A single periodic pipe acquires a seam twist at this self-crossing
    # projection. Four open splines avoid that kernel defect while retaining
    # the exact same centerline. Circular sections make the joins orientation
    # independent; small spherical unions make each join volumetric.
    ns, nl = 64, 32
    segment_defs = (
        (range(0, ns + 1), (1, 0, 0)),
        (range(ns, ns + nl + 1), (1, 0, 0)),
        (range(ns + nl, 2 * ns + nl + 1), (-1, 0, 0)),
        (list(range(2 * ns + nl, 2 * (ns + nl))) + [0], (-1, 0, 0)),
    )
    pieces = []
    for indices, start_tangent in segment_defs:
        segment = [pts[index] for index in indices]
        p0 = Vector(*segment[0])
        path = Edge.make_spline([Vector(*point) for point in segment])
        pieces.append(
            Solid.sweep(
                _circle_face(p0, start_tangent, P.rail_radius),
                path,
                make_solid=True,
            )
        )
    rail = Compound(children=pieces, label="continuous_figure_eight_rail")
    rail.label = "continuous_figure_eight_rail"
    rail.color = Color(0.08, 0.10, 0.16)
    return rail


def _segment_box(a, b, width: float, height: float, z_center: float):
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) + 0.65
    angle = math.degrees(math.atan2(dy, dx))
    return Box(length, width, height).moved(
        Location(((ax + bx) / 2.0, (ay + by) / 2.0, z_center), (0, 0, angle))
    )


def make_base_rib():
    pts = planar_route_points()
    ns, nl = 64, 32
    index_ranges = (
        range(0, ns + 1),
        range(ns, ns + nl + 1),
        range(ns + nl, 2 * ns + nl + 1),
        list(range(2 * ns + nl, 2 * (ns + nl))) + [0],
    )
    pieces = []
    for indices in index_ranges:
        segment = [Vector(*pts[index]) for index in indices]
        tangent = (segment[1] - segment[0]).normalized()
        side = Vector(0, 0, 1).cross(tangent).normalized()
        half_width = P.base_rib_width / 2.0
        half_height = P.base_thickness / 2.0
        p0 = segment[0]
        profile = Face(
            Wire.make_polygon(
                [
                    p0 + side * half_width - Vector(0, 0, half_height),
                    p0 - side * half_width - Vector(0, 0, half_height),
                    p0 - side * half_width + Vector(0, 0, half_height),
                    p0 + side * half_width + Vector(0, 0, half_height),
                ],
                close=True,
            )
        )
        pieces.append(
            Solid.sweep(
                profile,
                Edge.make_spline(segment),
                make_solid=True,
            )
        )
    # The two central ribbons overlap at both projected crossings. Finite port
    # pads join each lobe without the faceted knife wedges of segment boxes.
    rib = pieces[0].fuse(pieces[2]).clean()
    for x in (-P.half_straight, P.half_straight):
        for y in (-P.strand_offset, P.strand_offset):
            rib = rib.fuse(
                Solid.make_cylinder(
                    P.base_rib_width / 2.0 + 0.10,
                    P.base_thickness,
                    plane=Plane(origin=Vector(x, y, 0)),
                )
            ).clean()
    rib = rib.fuse(pieces[1], pieces[3]).clean()
    rib.label = "open_route_base_rib"
    return rib


def _is_upper_bridge_gap(x: float, y: float, z: float) -> bool:
    if z < P.low_rail_z + 4.0:
        return False
    for crossing in (-P.crossing_x, P.crossing_x):
        if math.hypot(x - crossing, y) < P.support_clear_radius:
            return True
    return False


def make_support_webs():
    pts = route_points()
    pieces = []
    for i in range(0, len(pts), 4):
        x, y, z = pts[i]
        if _is_upper_bridge_gap(x, y, z):
            continue
        height = z + 1.20 - P.base_thickness
        pieces.append(
            Solid.make_cylinder(
                P.web_thickness / 2.0,
                height,
                plane=Plane(origin=Vector(x, y, P.base_thickness)),
            )
        )
    webs = Compound(children=pieces, label="runner_slot_support_posts")
    webs.label = "runner_slot_support_web"
    return webs


def make_outer_frame():
    x_span = 2.0 * P.frame_outer_x
    y_span = 2.0 * P.frame_outer_y
    zc = P.base_thickness / 2.0
    pieces = [
        Box(x_span, P.frame_width, P.base_thickness).moved(
            Location((0, P.frame_outer_y - P.frame_width / 2.0, zc))
        ),
        Box(x_span, P.frame_width, P.base_thickness).moved(
            Location((0, -P.frame_outer_y + P.frame_width / 2.0, zc))
        ),
        Box(P.frame_width, y_span, P.base_thickness).moved(
            Location((P.frame_outer_x - P.frame_width / 2.0, 0, zc))
        ),
        Box(P.frame_width, y_span, P.base_thickness).moved(
            Location((-P.frame_outer_x + P.frame_width / 2.0, 0, zc))
        ),
    ]
    frame = pieces[0].fuse(*pieces[1:]).clean()
    frame.label = "bold_open_hand_frame"
    return frame


def make_runner():
    # Home is the far-left lobe midpoint. Its tangent is +Y, so the collar axis
    # is Y and the C opening faces -Z around the support posts. Five overlapping
    # prismatic strokes give the moon/C silhouette a finite 2.6 mm wall at both
    # horns; a cut annulus produced knife wedges where its slot met the circle.
    center = (-P.half_straight - P.lobe_radius_x, 0.0, P.low_rail_z)
    outer = P.runner_outer_radius
    inner = P.runner_inner_radius
    throat = P.runner_slot_width / 2.0
    cx, cy, cz = center
    y_start = cy - P.runner_length / 2.0
    profile = [
        (cx - throat, y_start, cz - outer),
        (cx - outer, y_start, cz - outer),
        (cx - outer, y_start, cz + outer),
        (cx + outer, y_start, cz + outer),
        (cx + outer, y_start, cz - outer),
        (cx + throat, y_start, cz - outer),
        (cx + throat, y_start, cz - inner),
        (cx + inner, y_start, cz - inner),
        (cx + inner, y_start, cz + inner),
        (cx - inner, y_start, cz + inner),
        (cx - inner, y_start, cz - inner),
        (cx - throat, y_start, cz - inner),
    ]
    runner = Solid.extrude(
        Face(Wire.make_polygon(profile, close=True)),
        (0, P.runner_length, 0),
    ).clean()
    runner.label = "captive_crescent_runner"
    runner.color = Color(0.72, 0.34, 0.08)
    return runner


def make_track_body():
    frame = make_outer_frame()
    rib = make_base_rib()
    webs = make_support_webs()
    rail = make_rail()
    body = frame.fuse(rib).clean()
    for support_post in webs.solids():
        body = body.fuse(support_post).clean()
    for rail_segment in rail.solids():
        body = body.fuse(rail_segment).clean()
    # The four pipe sections are tangent at the strand/lobe ports. A sphere
    # just 0.01 mm larger than the rail removes zero-area seam faces while
    # preserving the 4.4 mm nominal running surface within mesh tolerance.
    seam_radius = P.rail_radius + 0.01
    for seam in (
        (-P.half_straight, P.strand_offset, P.low_rail_z),
        (P.half_straight, P.strand_offset, P.low_rail_z),
        (P.half_straight, -P.strand_offset, P.low_rail_z),
        (-P.half_straight, -P.strand_offset, P.low_rail_z),
        (0.0, P.strand_offset, P.low_rail_z),
        (0.0, -P.strand_offset, P.low_rail_z),
    ):
        body = body.fuse(
            Solid.make_sphere(seam_radius, plane=Plane(origin=Vector(*seam)))
        ).clean()
    # Give every post/rail junction the same finite spherical blend. Without
    # it, an otherwise watertight mesh retained isolated sub-nozzle wedges at
    # whichever oblique post happened to align with the voxel grid.
    route = route_points()
    support_blend_radius = P.rail_radius + 0.02
    for i in range(0, len(route), 4):
        point = route[i]
        if _is_upper_bridge_gap(*point):
            continue
        body = body.fuse(
            Solid.make_sphere(
                support_blend_radius,
                plane=Plane(origin=Vector(*point)),
            )
        ).clean()
    body.label = "braided_track_and_frame"
    body.color = Color(0.08, 0.10, 0.16)
    assert len(body.solids()) == 1, "Track/frame must remain one connected solid"
    return body


def make_assembly():
    track = make_track_body()
    runner = make_runner()
    assembly = Compound(children=[track, runner], label="Eclipse Braid")
    assert len(assembly.solids()) == 2, "Print-in-place output requires track and runner"
    return assembly
