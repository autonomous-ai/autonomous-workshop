"""One-piece support-free C-mouth bezel with outer rib and four posts."""

import math
from build123d import fillet
from cadgen.assembly import label_shape
from features.common import cylinder_from
from features.profiles import polar_sector
import params as p


def _rounded_sector(r0, r1, a0, a1):
    sector = polar_sector(r0, r1, a0, a1, p.LIP_T)
    endpoints = [p.polar_xy(radius, angle) for radius in (r0, r1) for angle in (a0, a1)]
    end_edges = [
        edge
        for edge in sector.edges()
        if abs(edge.length - p.LIP_T) < 0.01
        and min(math.hypot(edge.center().X - x, edge.center().Y - y) for x, y in endpoints) < 0.1
    ]
    return fillet(end_edges, radius=0.8)


def build_mouth_bezel():
    upper = _rounded_sector(p.LIP_R_IN, p.LIP_R_OUT, p.UPPER_LIP_A0, p.UPPER_LIP_A1)
    lower = _rounded_sector(p.LIP_R_IN, p.LIP_R_OUT, p.LOWER_LIP_A0, p.LOWER_LIP_A1)
    rib = _rounded_sector(p.BEZEL_JOIN_R0, p.BEZEL_JOIN_R1, p.UPPER_LIP_A0, p.LOWER_LIP_A1)
    result = upper + lower + rib
    for angle in p.BEZEL_PILOT_ANGLES:
        x, y = p.polar_xy(p.LIP_STANDOFF_R, angle)
        result = result + cylinder_from(
            p.BEZEL_POST_D / 2.0, p.LIP_STANDOFF_L + p.FUSE_OVERLAP,
            z=p.LIP_T - p.MIN_WALL, x=x, y=y,
        )
    return label_shape(result, "c_mouth_bezel")
