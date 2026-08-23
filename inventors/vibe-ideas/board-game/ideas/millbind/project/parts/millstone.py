"""Millstone gears (mill_gear_tri/square/penta/hex): full-height tooth
barrel + furrowed grinding disc + a prism hub (3/4/5/6 flats) that is a
player's whole identity for the game -- read by counting flats, never by
colour. Identical barrel/crown across all four; only the hub flat-count
differs.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params
from parts.gears import build_barrel, bore_through


def _polygon_pts(n: int, across_flats: float, rot_deg: float = 0.0) -> list[tuple[float, float]]:
    circum_r = (across_flats / 2.0) / math.cos(math.pi / n)
    pts = []
    for i in range(n):
        a = math.radians(rot_deg + i * 360.0 / n)
        pts.append((circum_r * math.cos(a), circum_r * math.sin(a)))
    return pts


def _furrowed_crown(p: Params) -> cq.Workplane:
    """`crown_d`/`crown_h` grinding disc, `crown_furrow_depth`-deep radial
    furrows (the harp pattern of a real millstone)."""
    crown = cq.Workplane("XY").circle(p.crown_d / 2.0).extrude(p.crown_h)
    n_furrows = 8
    groove_w = 2.2
    for i in range(n_furrows):
        angle = i * 360.0 / n_furrows
        groove = (
            cq.Workplane("XY")
            .rect(p.crown_d, groove_w, centered=True)
            .extrude(p.crown_furrow_depth)
            .translate((p.crown_d / 4.0, 0, p.crown_h - p.crown_furrow_depth))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        crown = crown.cut(groove)
    return crown


def make_mill_gear(p: Params, n_flats: int) -> cq.Workplane:
    barrel = build_barrel(p, p.barrel_h, p.barrel_teeth_z0, p.barrel_teeth_z1)
    crown = _furrowed_crown(p).translate((0, 0, p.barrel_h))
    hub = (
        cq.Workplane("XY")
        .polyline(_polygon_pts(n_flats, p.hub_across_flats))
        .close()
        .extrude(p.hub_h)
        .translate((0, 0, p.barrel_h + p.crown_h))
    )
    body = barrel.union(crown).union(hub)
    body = bore_through(p, body, p.barrel_h)
    return body
