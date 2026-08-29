"""Gravity-drop bayonet cap with keeper-blocking skirt."""

from __future__ import annotations

from build123d import Align, Box, Cylinder, Location

import params as p
from features.primitives import annulus, rounded_radial_box


def build_cap():
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    shoulder_local = p.CAP_SHOULDER_Z - p.CAP_BOTTOM_Z
    cap = Location((0, 0, shoulder_local)) * (Cylinder(p.CAP_RADIUS, p.CAP_TOP_Z - p.CAP_SHOULDER_Z, align=alignment) - Cylinder(p.CAP_BORE_RADIUS, p.CAP_TOP_Z - p.CAP_SHOULDER_Z + 0.2, align=alignment))
    cap += annulus(p.CAP_SKIRT_RADII[1], p.CAP_SKIRT_RADII[0], shoulder_local)
    collar = Location((0, 0, shoulder_local)) * annulus(8.0, p.CAP_BORE_RADIUS, 5.0)
    cap += collar
    # One symmetric through-channel makes the opposed ear paths exact 180-degree
    # copies and avoids knife-edge residuals where two separate pockets meet the bore.
    pocket = rounded_radial_box(
        16.0,
        p.CAP_SLOT_THROAT,
        p.CAP_POCKET_HEIGHT + p.CAP_GRAVITY_DROP + 0.5,
        0.6,
        0.0,
        -p.CAP_LOCK_ROTATION_DEG,
        p.EAR_BOTTOM_Z - p.CAP_BOTTOM_Z - p.CAP_GRAVITY_DROP - 0.3,
    )
    cap -= pocket
    ear_clearance = Location((0, 0, p.EAR_BOTTOM_Z - p.CAP_BOTTOM_Z - p.CAP_GRAVITY_DROP - 0.3)) * Cylinder(
        8.0,
        p.CAP_POCKET_HEIGHT + p.CAP_GRAVITY_DROP + 0.5,
        align=alignment,
    )
    cap -= ear_clearance
    return cap
