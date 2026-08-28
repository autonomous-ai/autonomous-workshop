"""Broad wheel, hub, skirt, spokes, and open follower cage."""

from __future__ import annotations

from build123d import Align, Box, CenterArc, Cylinder, Location, SlotArc, Solid, Torus, Vector

import params as p
from features.primitives import annulus, half_annulus, radial_box, rounded_radial_box


def build_wheel():
    z0 = p.CAGE_BOTTOM_Z
    ring = Location((0, 0, p.WHEEL_RING_BOTTOM_Z - z0)) * annulus(p.WHEEL_RING_OUTER_RADIUS, p.WHEEL_RING_INNER_RADIUS, p.WHEEL_RING_TOP_Z - p.WHEEL_RING_BOTTOM_Z)
    skirt = Location((0, 0, p.WHEEL_SKIRT_BOTTOM_Z - z0)) * annulus(p.WHEEL_SKIRT_OUTER_RADIUS, p.WHEEL_SKIRT_INNER_RADIUS, p.WHEEL_RING_TOP_Z - p.WHEEL_SKIRT_BOTTOM_Z)
    ring += skirt
    ring_top_z = p.WHEEL_RING_TOP_Z - z0
    ring_top_edges = [
        edge for edge in ring.edges() if abs(edge.center().Z - ring_top_z) < 1e-6
    ]
    ring = ring.fillet(3.2, ring_top_edges)
    skirt_bottom_z = p.WHEEL_SKIRT_BOTTOM_Z - z0
    skirt_bottom_edges = [
        edge for edge in ring.edges() if abs(edge.center().Z - skirt_bottom_z) < 1e-6
    ]
    ring = ring.fillet(0.3, skirt_bottom_edges)
    ring_inner_bottom_edges = [
        edge
        for edge in ring.edges()
        if abs(edge.center().Z - (p.WHEEL_RING_BOTTOM_Z - z0)) < 1e-6
        and abs((edge.center().X**2 + edge.center().Y**2) ** 0.5 - p.WHEEL_RING_INNER_RADIUS) < 0.1
    ]
    ring = ring.fillet(1.5, ring_inner_bottom_edges)
    groove_tool_radius = 0.4
    groove_z = p.WHEEL_RING_TOP_Z - z0 + groove_tool_radius - p.GRIP_GROOVE_DEPTH
    for groove_radius in p.GRIP_GROOVE_RADII:
        for start_angle in (28.0, 208.0):
            groove = Location((0, 0, groove_z)) * Torus(
                groove_radius,
                groove_tool_radius,
                major_angle=124.0,
                rotation=(0, 0, start_angle),
            )
            ring -= groove
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    lower_hub = annulus(
        p.WHEEL_HUB_RADIUS,
        p.WHEEL_BORE_RADIUS,
        25.0 - p.WHEEL_HUB_BOTTOM_Z,
    )
    hub = Location((0, 0, p.WHEEL_HUB_BOTTOM_Z - z0)) * lower_hub

    # The cap blocks the keeper in normal use, but after the cap is removed the
    # keeper must be able to slide radially inward through the upper bearing.
    # Model that service opening directly as a broad C, instead of subtracting
    # tangent cutters that leave zero-thickness cusps at the bore.
    def c_annulus(inner_radius: float, height: float):
        center_radius = (p.WHEEL_HUB_RADIUS + inner_radius) / 2.0
        radial_width = p.WHEEL_HUB_RADIUS - inner_radius
        center_arc = CenterArc(
            (0, 0),
            center_radius,
            p.WHEEL_SERVICE_C_START_DEG,
            p.WHEEL_SERVICE_C_SPAN_DEG,
        )
        rounded_sector = SlotArc(center_arc, radial_width)
        return Solid.extrude(rounded_sector.face(), Vector(0, 0, height))

    service_hub = Location((0, 0, p.WHEEL_UPPER_HUB_START_Z - z0)) * c_annulus(
        p.WHEEL_BORE_RADIUS,
        p.WHEEL_HUB_TOP_Z - p.WHEEL_UPPER_HUB_START_Z,
    )
    hub += service_hub
    hub = hub.clean()
    tab_service_z = 31.0 - p.CAGE_BOTTOM_Z - p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE
    tab_service_height = (
        p.WHEEL_HUB_TOP_Z
        - (31.0 - p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE)
        + 2.2
    )
    wheel = ring + hub
    spoke_z = p.WHEEL_RING_BOTTOM_Z - z0
    spoke_length = p.WHEEL_RING_INNER_RADIUS - p.WHEEL_HUB_RADIUS + 5.0
    for angle in (0.0, 120.0, 240.0):
        spoke = radial_box(
            spoke_length,
            8.0,
            4.0,
            (p.WHEEL_RING_INNER_RADIUS + p.WHEEL_HUB_RADIUS) / 2.0,
            angle,
            spoke_z,
        )
        spoke_edges = [edge for edge in spoke.edges() if abs(edge.length - spoke_length) < 1e-6]
        wheel += spoke.fillet(1.5, spoke_edges)
    cage = Location((p.FOLLOWER_CENTER_RADIUS, 0, 0)) * annulus(p.CAGE_RADIUS, p.CAGE_INNER_RADIUS, p.CAGE_TOP_Z - p.CAGE_BOTTOM_Z)
    opening = Location((p.FOLLOWER_CENTER_RADIUS - p.CAGE_RADIUS - 1.0, -p.CAGE_RADIUS, -0.1)) * Box(
        p.CAGE_RADIUS + 1.5,
        p.CAGE_RADIUS * 2.0,
        p.CAGE_TOP_Z - p.CAGE_BOTTOM_Z + 0.2,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    cage -= opening
    cage = cage.chamfer(0.8, None, cage.edges())
    wheel += cage
    wheel -= opening
    follower_clearance = Location((p.FOLLOWER_CENTER_RADIUS, 0, 0)) * Cylinder(
        p.CAGE_INNER_RADIUS,
        p.CAGE_TOP_Z - p.CAGE_BOTTOM_Z + 0.2,
        align=alignment,
    )
    wheel -= follower_clearance
    for land_bottom, land_top in p.GUIDE_LANDS_Z:
        fixed_land = half_annulus(
            p.CAGE_INNER_RADIUS + 0.25,
            p.GUIDE_BORE_RADIUS,
            land_top - land_bottom,
            inward=False,
        )
        wheel += Location((
            p.FOLLOWER_CENTER_RADIUS,
            0,
            land_bottom - p.CAGE_BOTTOM_Z,
        )) * fixed_land
    rail_local_z = p.KEEPER_RAIL_Z[0] - p.CAGE_BOTTOM_Z - p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE
    rail_height = (
        p.KEEPER_RAIL_Z[1]
        - p.KEEPER_RAIL_Z[0]
        + 2.0 * p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE
    )
    for y in (
        -p.KEEPER_WIDTH / 2.0 - p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
        p.KEEPER_WIDTH / 2.0 - 2.0 - p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
    ):
        rail_clearance = Location((
            p.KEEPER_INNER_EDGE_RADIUS - p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
            y,
            rail_local_z,
        )) * Box(
            p.KEEPER_LENGTH + 2.0 * p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
            2.0 + 2.0 * p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
            rail_height,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        wheel -= rail_clearance
    keeper_service_start = p.WHEEL_HUB_RADIUS - 0.5
    keeper_service_end = (
        p.KEEPER_INNER_EDGE_RADIUS
        + p.KEEPER_LENGTH
        + p.KEEPER_DOVETAIL_SIDE_CLEARANCE
    )
    keeper_service_length = keeper_service_end - keeper_service_start
    keeper_service_channel = rounded_radial_box(
        keeper_service_length,
        p.KEEPER_WIDTH + 8.0,
        p.KEEPER_RAIL_Z[1] - p.KEEPER_RAIL_Z[0] + 2.0 * p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE,
        (
            p.KEEPER_RAIL_Z[1]
            - p.KEEPER_RAIL_Z[0]
            + 2.0 * p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE
        ) / 2.0,
        keeper_service_start + keeper_service_length / 2.0,
        0.0,
        p.KEEPER_RAIL_Z[0] - p.CAGE_BOTTOM_Z - p.KEEPER_DOVETAIL_VERTICAL_CLEARANCE,
        round_ends=False,
    )
    wheel -= keeper_service_channel
    keeper_service_mid_z = (
        (p.KEEPER_RAIL_Z[0] + p.KEEPER_RAIL_Z[1]) / 2.0 - p.CAGE_BOTTOM_Z
    )
    keeper_exit_edges = [
        edge
        for edge in wheel.edges()
        if abs(edge.center().Z - keeper_service_mid_z) < 0.1
        and 13.5
        < ((edge.center().X - p.FOLLOWER_CENTER_RADIUS) ** 2 + edge.center().Y**2) ** 0.5
        < 14.5
        and abs(edge.center().Y) > 10.0
    ]
    wheel = wheel.fillet(1.0, keeper_exit_edges)
    lower_service_start = p.FOLLOWER_CENTER_RADIUS - p.CAGE_RADIUS - 1.0
    lower_service_length = p.CAGE_RADIUS + 1.5
    lower_guide_service_channel = rounded_radial_box(
        lower_service_length,
        2.0 * (p.PLECTRUM_FLANGE_RADIUS + p.KEEPER_DOVETAIL_SIDE_CLEARANCE),
        p.GUIDE_LANDS_Z[0][1] - p.GUIDE_LANDS_Z[0][0] + 0.4,
        1.0,
        lower_service_start + lower_service_length / 2.0,
        0.0,
        p.GUIDE_LANDS_Z[0][0] - p.CAGE_BOTTOM_Z - 0.2,
        round_ends=False,
    )
    wheel -= lower_guide_service_channel
    tab_service_start = p.WHEEL_HUB_RADIUS - 0.5
    tab_service_end = p.KEEPER_INNER_EDGE_RADIUS + 7.0 + p.KEEPER_DOVETAIL_SIDE_CLEARANCE
    tab_service_length = tab_service_end - tab_service_start
    keeper_tab_service_channel = rounded_radial_box(
        tab_service_length,
        8.0 + 2.0 * p.KEEPER_DOVETAIL_SIDE_CLEARANCE,
        tab_service_height,
        2.0,
        tab_service_start + tab_service_length / 2.0,
        0.0,
        tab_service_z,
        round_ends=False,
    )
    wheel -= keeper_tab_service_channel
    counter_base_z = p.WHEEL_RING_TOP_Z - z0
    counter = Location((
        -p.FOLLOWER_CENTER_RADIUS,
        0,
        counter_base_z,
    )) * Cylinder(p.COUNTERWEIGHT_RADIUS, 2.0, align=alignment)
    counter = counter.fillet(0.9, counter.edges())
    counter_neck = Location((
        -p.FOLLOWER_CENTER_RADIUS,
        0,
        counter_base_z - 1.0,
    )) * Cylinder(9.0, 1.8, align=alignment)
    counter_neck = counter_neck.fillet(0.6, counter_neck.edges())
    wheel += counter + counter_neck
    return wheel.clean()
