"""Rigid rail-and-half-land follower keeper."""

from __future__ import annotations

from build123d import Align, Box, Location

import params as p
from features.primitives import half_annulus


def build_follower_keeper():
    alignment = (Align.MIN, Align.MIN, Align.MIN)
    inner_x = p.KEEPER_INNER_EDGE_RADIUS
    rail_len = p.KEEPER_LENGTH
    rail_z0, rail_z1 = p.KEEPER_RAIL_Z
    keeper = None
    for y in (-p.KEEPER_WIDTH / 2.0, p.KEEPER_WIDTH / 2.0 - 2.0):
        rail = Location((inner_x, y, rail_z0 - 28.0)) * Box(rail_len, 2.0, rail_z1 - rail_z0, align=alignment)
        keeper = rail if keeper is None else keeper + rail
    for land_bottom, land_top in p.GUIDE_LANDS_Z:
        half = half_annulus(p.PLECTRUM_FLANGE_RADIUS, p.GUIDE_BORE_RADIUS, land_top - land_bottom, inward=True)
        keeper += Location((p.FOLLOWER_CENTER_RADIUS, 0, land_bottom - 28.0)) * half
    tab = Location((inner_x, -4.0, 3.0)) * Box(7.0, 8.0, 5.0, align=alignment)
    keeper += tab
    inner_crossbar = Location((inner_x, -p.KEEPER_WIDTH / 2.0, rail_z0 - 28.0)) * Box(
        7.0,
        p.KEEPER_WIDTH,
        rail_z1 - rail_z0,
        align=alignment,
    )
    keeper += inner_crossbar
    for y in (-6.25, 5.0):
        guide_bridge = Location((p.FOLLOWER_CENTER_RADIUS - 2.0, y, 3.0)) * Box(
            2.0,
            1.25,
            rail_z1 - 31.0,
            align=alignment,
        )
        keeper += guide_bridge
    return keeper
