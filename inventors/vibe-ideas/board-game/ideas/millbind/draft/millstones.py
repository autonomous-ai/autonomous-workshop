"""Millstone gears: full-height tooth barrel + furrowed grinding disc +
a prism hub (3/4/5/6 flats) that is a player's whole identity for the game.
"""
import math

import cadquery as cq

import params as p
from gears import build_barrel, bore_through


def _polygon_pts(n: int, across_flats: float, rot_deg: float = 0.0):
    circum_r = (across_flats / 2.0) / math.cos(math.pi / n)
    pts = []
    for i in range(n):
        a = math.radians(rot_deg + i * 360.0 / n)
        pts.append((circum_r * math.cos(a), circum_r * math.sin(a)))
    return pts


def _furrowed_crown() -> cq.Workplane:
    """34mm/6mm grinding disc, 1.2mm-deep radial furrows (the harp pattern)."""
    crown = cq.Workplane("XY").circle(p.CROWN_D / 2.0).extrude(p.CROWN_H)
    n_furrows = 8
    groove_w = 2.2
    for i in range(n_furrows):
        angle = i * 360.0 / n_furrows
        groove = (
            cq.Workplane("XY")
            .rect(p.CROWN_D, groove_w, centered=True)
            .extrude(p.CROWN_FURROW_DEPTH)
            .translate((p.CROWN_D / 4.0, 0, p.CROWN_H - p.CROWN_FURROW_DEPTH))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        crown = crown.cut(groove)
    return crown


def build_mill_gear(n_flats: int) -> cq.Workplane:
    barrel = build_barrel(p.BARREL_H, p.BARREL_TEETH_Z0, p.BARREL_TEETH_Z1)
    crown = _furrowed_crown().translate((0, 0, p.BARREL_H))
    hub = (
        cq.Workplane("XY")
        .polyline(_polygon_pts(n_flats, p.HUB_ACROSS_FLATS))
        .close()
        .extrude(p.HUB_H)
        .translate((0, 0, p.BARREL_H + p.CROWN_H))
    )
    body = barrel.union(crown).union(hub)
    body = bore_through(body, p.BARREL_H)
    return body
