"""Three-chamber resonator bowl, guard, and spindle."""

from __future__ import annotations

import math

from build123d import Align, Box, Cylinder, Location

import params as p
from features.primitives import annulus, polar_sector, radial_box, rounded_radial_box


def _chamber_cuts():
    cuts = []
    for key, start in (("rain", 0.0), ("frog_song", 120.0), ("crickets", 240.0)):
        depth = p.CHAMBER_DEPTHS[key]
        cut = polar_sector(p.CHAMBER_INNER_RADIUS, p.CHAMBER_OUTER_RADIUS, start, p.FIELD_SPAN_DEG, depth + 0.2)
        cuts.append(Location((0, 0, p.BASE_BODY_TOP - depth)) * cut)
    return cuts


def _port_cut(width: float, angle_deg: float, radial_start: float, radial_end: float):
    return rounded_radial_box(
        radial_end - radial_start + 2.0,
        width,
        p.PORT_HEIGHT,
        p.PORT_FILLET_RADIUS,
        (radial_start + radial_end) / 2.0,
        angle_deg,
        p.PORT_CENTER_Z - p.PORT_HEIGHT / 2.0,
    )


def _frog_curved_port():
    width = p.PORT_WIDTHS["frog_song"]
    path = Location((0, 0, p.PORT_CENTER_Z - p.PORT_HEIGHT / 2.0)) * polar_sector(
        p.FROG_NECK_RADIUS - width / 2.0,
        p.FROG_NECK_RADIUS + width / 2.0,
        p.FROG_NECK_START_DEG,
        p.FROG_NECK_END_DEG - p.FROG_NECK_START_DEG,
        p.PORT_HEIGHT,
    )
    exit_cut = _port_cut(p.PORT_WIDTHS["frog_song"], p.PORT_EXIT_ANGLES["frog_song"], 49.0, 61.0)
    return path + exit_cut


def build_base():
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Cylinder(p.PRODUCT_RADIUS, p.BASE_FLOOR, align=alignment)
    body += Cylinder(p.GUARD_OUTER_RADIUS + 0.6, p.BASE_BODY_TOP, align=alignment)
    for cut in _chamber_cuts():
        body -= cut
    for key in ("rain", "frog_song", "crickets"):
        body -= radial_box(
            4.0,
            p.PORT_WIDTHS[key] + 5.0,
            p.PORT_HEIGHT + 4.0,
            60.0,
            p.PORT_EXIT_ANGLES[key],
            p.PORT_CENTER_Z - p.PORT_HEIGHT / 2.0 - 2.0,
        )
    body -= _port_cut(p.PORT_WIDTHS["rain"], p.PORT_EXIT_ANGLES["rain"], 48.0, 61.0)
    body -= _frog_curved_port()
    body -= _port_cut(p.PORT_WIDTHS["crickets"], p.PORT_EXIT_ANGLES["crickets"], 49.0, 61.0)
    terrace = Location((0, 0, p.BASE_BODY_TOP)) * annulus(p.PRODUCT_RADIUS, p.GUARD_INNER_RADIUS, p.GUARD_BOTTOM_Z - p.BASE_BODY_TOP + 0.2)
    guard = Location((0, 0, p.GUARD_BOTTOM_Z)) * annulus(p.GUARD_OUTER_RADIUS, p.GUARD_INNER_RADIUS, p.GUARD_TOP_Z - p.GUARD_BOTTOM_Z)
    spindle = Cylinder(p.SPINDLE_PEDESTAL_RADIUS, p.SPINDLE_PEDESTAL_TOP, align=alignment)
    spindle += Location((0, 0, p.JOURNAL_BOTTOM_Z)) * Cylinder(p.JOURNAL_RADIUS, p.JOURNAL_TOP_Z - p.JOURNAL_BOTTOM_Z, align=alignment)
    neck = Location((0, 0, p.JOURNAL_TOP_Z)) * Cylinder(
        p.NECK_RADIUS,
        p.NECK_TOP_Z - p.JOURNAL_TOP_Z,
        align=alignment,
    )
    neck = neck.fillet(0.5, neck.edges())
    spindle += neck
    for angle in (0.0, 180.0):
        ear = radial_box(
            p.EAR_RADIAL_TIP - p.NECK_RADIUS + 0.2,
            p.EAR_TANGENTIAL_WIDTH,
            p.EAR_TOP_Z - p.EAR_BOTTOM_Z,
            (p.EAR_RADIAL_TIP + p.NECK_RADIUS) / 2.0 - 0.1,
            angle,
            p.EAR_BOTTOM_Z,
        )
        ear = ear.fillet(0.4, ear.edges())
        spindle += ear
    foot = annulus(58.0, 54.0, 1.0)
    base = body + terrace + guard + spindle + foot
    for exit_angle in p.PORT_EXIT_ANGLES.values():
        port_edges = []
        for edge in base.edges():
            center = edge.center()
            radius = math.hypot(center.X, center.Y)
            angle = math.degrees(math.atan2(center.Y, center.X)) % 360.0
            angle_delta = abs((angle - exit_angle + 180.0) % 360.0 - 180.0)
            if radius > 47.0 and 8.0 < center.Z < 13.0 and angle_delta < 10.0:
                port_edges.append(edge)
        base = base.fillet(p.PORT_FILLET_RADIUS, port_edges)
    deck_rim_edges = [
        edge for edge in base.edges()
        if abs(edge.center().Z - p.BASE_BODY_TOP) < 0.25
    ]
    base = base.chamfer(0.8, None, deck_rim_edges)
    guard_top_edges = [
        edge for edge in base.edges()
        if abs(edge.center().Z - p.GUARD_TOP_Z) < 0.25
    ]
    base = base.fillet(0.8, guard_top_edges)
    return base
