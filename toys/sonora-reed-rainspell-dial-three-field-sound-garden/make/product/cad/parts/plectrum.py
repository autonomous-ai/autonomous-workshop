"""Captive gravity follower; local tip datum is z=0."""

from __future__ import annotations

from build123d import Align, Box, Cone, Cylinder, Sphere, Location

import params as p


def build_plectrum():
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    tip = Location((0, 0, p.PLECTRUM_TIP_RADIUS)) * Sphere(p.PLECTRUM_TIP_RADIUS)
    tip &= Box(
        p.PLECTRUM_TIP_RADIUS * 2.0,
        p.PLECTRUM_TIP_RADIUS * 2.0,
        p.PLECTRUM_TIP_RADIUS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flange = Location((0, 0, p.PLECTRUM_FLANGE_Z[0])) * Cylinder(p.PLECTRUM_FLANGE_RADIUS, p.PLECTRUM_FLANGE_Z[1] - p.PLECTRUM_FLANGE_Z[0], align=alignment)
    shoulder = Location((0, 0, p.PLECTRUM_FLANGE_Z[1])) * Cone(p.PLECTRUM_FLANGE_RADIUS, p.PLECTRUM_STEM_RADIUS, p.PLECTRUM_SHOULDER_TOP - p.PLECTRUM_FLANGE_Z[1], align=alignment)
    stem = Location((0, 0, p.PLECTRUM_SHOULDER_TOP)) * Cylinder(p.PLECTRUM_STEM_RADIUS, p.PLECTRUM_STEM_TOP - p.PLECTRUM_SHOULDER_TOP, align=alignment)
    head = Location((0, 0, p.PLECTRUM_STEM_TOP)) * Cylinder(p.PLECTRUM_HEAD_RADIUS, p.PLECTRUM_HEAD_TOP - p.PLECTRUM_STEM_TOP, align=alignment)
    return tip + flange + shoulder + stem + head
