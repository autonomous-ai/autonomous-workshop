"""Parametric rounded-tooth printed spur gears from governing numbers."""

import math
from build123d import fillet
from features.common import prism


def spur_gear(
    module: float,
    teeth: int,
    thickness: float,
    pressure_angle_deg: float,
    backlash: float = 0.0,
    axial_fillet: float = 0.25,
):
    if teeth < 8 or module <= 0 or thickness <= 0:
        raise ValueError("invalid gear parameters")
    rp = module * teeth / 2.0
    ra = rp + module * 0.90 - backlash / 2.0
    rd = max(module, rp - module * 1.10)
    # One continuous periodic outline avoids weak tooth/root Boolean wedges.
    # Sixteen samples per tooth leave smoothly rounded printable lobes while
    # preserving the governed pitch radius, tooth count and 2:1 ratio.
    pressure_bias = max(0.80, math.cos(math.radians(pressure_angle_deg)))
    mid_radius = (ra + rd) / 2.0
    amplitude = (ra - rd) / 2.0 * pressure_bias
    point_count = teeth * 16
    points = []
    for i in range(point_count):
        angle = 2.0 * math.pi * i / point_count
        radius = mid_radius + amplitude * math.cos(teeth * angle)
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    result = prism(points, thickness)
    if axial_fillet > 0.0:
        axial_edges = [
            edge
            for edge in result.edges()
            if abs(edge.center().Z) < 1e-6 or abs(edge.center().Z - thickness) < 1e-6
        ]
        result = fillet(axial_edges, radius=min(axial_fillet, thickness / 8.0))
    result.label = f"printed_{teeth}t_gear"
    return result


def gear_pitch_radius(module: float, teeth: int) -> float:
    return module * teeth / 2.0
