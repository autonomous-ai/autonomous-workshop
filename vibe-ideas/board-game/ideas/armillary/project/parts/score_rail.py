"""score_rail — one per seat: a plain front slot for open catches and a
raised rear (zenith) slot for zenith winnings, stood on edge. Four rails
share one profile and differ only by end-finial cross-section, so a rail
belongs to a seat by shape alone.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params


def _cut_slot(bar: cq.Workplane, p: Params, y_center: float, top_z: float) -> cq.Workplane:
    slot = (
        cq.Workplane("XY")
        .rect(p.rail_slot_len, p.rail_slot_w)
        .extrude(p.rail_slot_depth + 1.0)
        .translate((0, y_center, top_z - p.rail_slot_depth))
    )
    return bar.cut(slot)


def _finial(p: Params, sides: int) -> cq.Workplane:
    """A short prism boss on one end of the rail; cross-section shape is
    the only thing that tells the four rails apart.

    The finial projects past the bar's own end face (x = rail_len/2), so
    nothing in the bar body sits underneath it -- it must reach z=0 (the
    bar's own bed-contact plane) on its own or it prints as a floating
    island for however many mm its lowest point sits above the bed.
    Centering it on rail_h/2 (the old code) left it floating from z=6mm
    up. Anchor it at its own lowest vertex instead, so its z-extent starts
    exactly at the bed/bar-bottom plane regardless of polygon shape."""
    pts = []
    for i in range(sides):
        ang = math.radians(90 + i * 360.0 / sides)
        pts.append((p.rail_finial_r * math.cos(ang), p.rail_finial_r * math.sin(ang)))
    min_z = min(b for _, b in pts)
    profile = cq.Workplane("YZ").polyline(pts).close().extrude(p.rail_finial_len)
    return profile.translate((p.rail_len / 2.0, 0, -min_z))


_FINIALS = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6}


def make_score_rail(p: Params, finial: str) -> cq.Workplane:
    bar = cq.Workplane("XY").box(
        p.rail_len, p.rail_w, p.rail_h, centered=(True, True, False)
    )

    front_y = -p.rail_w / 4.0
    bar = _cut_slot(bar, p, front_y, p.rail_h)

    # Raised rear ledge carrying the zenith slot, stepped up above the
    # plain top so it reads distinct at a glance (and marked with a small
    # sunburst-motif tick row, echoing the plinth's zenith collar).
    rear_y = p.rail_w / 4.0
    ledge = (
        cq.Workplane("XY")
        .rect(p.rail_slot_len + 6.0, p.rail_w / 2.0 - 2.0)
        .extrude(p.rail_zenith_step_h)
        .translate((0, rear_y, p.rail_h))
    )
    bar = bar.union(ledge)
    bar = _cut_slot(bar, p, rear_y, p.rail_h + p.rail_zenith_step_h)

    # A small tick row on the raised ledge, echoing the plinth's sunburst
    # motif. Cut as explicit solids in the rail's own global frame rather
    # than via a top-face selector, since the ledge union above leaves more
    # than one candidate ">Z" face.
    ledge_top_z = p.rail_h + p.rail_zenith_step_h
    tick_y = rear_y + p.rail_w / 4.0 - 1.0
    for i in range(6):
        tx = -p.rail_slot_len / 2.0 + i * (p.rail_slot_len / 5.0)
        tick = (
            cq.Workplane("XY")
            .circle(0.9)
            .extrude(1.2 + 0.4)
            .translate((tx, tick_y, ledge_top_z - 1.2))
        )
        bar = bar.cut(tick)

    bar = bar.union(_finial(p, _FINIALS[finial]))
    return bar


def make_score_rail_tri(p: Params) -> cq.Workplane:
    return make_score_rail(p, "triangle")


def make_score_rail_square(p: Params) -> cq.Workplane:
    return make_score_rail(p, "square")


def make_score_rail_penta(p: Params) -> cq.Workplane:
    return make_score_rail(p, "pentagon")


def make_score_rail_hex(p: Params) -> cq.Workplane:
    return make_score_rail(p, "hexagon")
