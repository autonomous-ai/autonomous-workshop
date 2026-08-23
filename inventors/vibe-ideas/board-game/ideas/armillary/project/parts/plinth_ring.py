"""plinth_ring — the drum plinth: ten face-down tile wells + axle post.

Owns three numbers every other part derives from without restating: well
diameter (24mm), well depth (6mm), axle diameter (24mm).

Build order matters here: the flat top face is used as a selector target
(`.faces(">Z")`) for the index grooves and the constellation dots, so those
cuts happen while the top is still a single flat plane — BEFORE the zenith
collars (raised bosses) and the axle post (a much taller, smaller-diameter
cylinder) are unioned on, either of which would become the new ">Z" face and
steal the selector.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params
from blocks import cut_wells
from features.ring import RING_XY, RING_ANGLES


def _sunburst_collar(p: Params, cx: float, cy: float) -> cq.Workplane:
    """Raised ring + tooth notches marking a zenith well."""
    ring = (
        cq.Workplane("XY")
        .circle(p.zenith_collar_outer_r)
        .circle(p.zenith_collar_inner_r)
        .extrude(p.zenith_collar_h)
        .translate((cx, cy, p.plinth_drum_h))
    )
    teeth = 8
    for i in range(teeth):
        ang = math.radians(i * 360.0 / teeth)
        tx = cx + (p.zenith_collar_outer_r + 0.1) * math.cos(ang)
        ty = cy + (p.zenith_collar_outer_r + 0.1) * math.sin(ang)
        notch = (
            cq.Workplane("XY")
            .box(2.5, 2.5, p.zenith_collar_h + 0.4)
            .translate((tx, ty, p.plinth_drum_h + p.zenith_collar_h / 2))
        )
        ring = ring.cut(notch)
    return ring


def make_plinth_ring(p: Params) -> cq.Workplane:
    r = p.plinth_dia / 2.0
    drum = cq.Workplane("XY").circle(r).extrude(p.plinth_drum_h)
    drum = drum.edges("<Z").chamfer(p.plinth_skirt_chamfer)

    # ---- ten wells on the shared 80mm-radius ring, one thumb scallop each
    positions = [(x, y, 0.0) for x, y in RING_XY]
    drum = cut_wells(
        drum, positions, diameter=p.well_dia, depth=p.well_depth,
        top_z=p.plinth_drum_h,
    )

    # ---- ten index grooves on the top rim ledge, one per shared ring angle
    groove_r = r - 5.0
    groove_pts = [
        (groove_r * math.cos(math.radians(a)), groove_r * math.sin(math.radians(a)))
        for a in RING_ANGLES
    ]
    drum = (
        drum.faces(">Z")
        .workplane()
        .pushPoints(groove_pts)
        .circle(p.index_groove_dia / 2.0)
        .cutBlind(-p.index_groove_depth)
    )

    # ---- constellation relief: a light scatter of engraved dots on the
    # outer rim ledge (between the well ring and the outer edge), well clear
    # of wells / collars / axle.
    dot_r = r - 12.0
    dot_angles = [a + 18.0 for a in RING_ANGLES]  # offset from the grooves
    dot_pts = [
        (dot_r * math.cos(math.radians(a)), dot_r * math.sin(math.radians(a)))
        for a in dot_angles
    ]
    drum = (
        drum.faces(">Z")
        .workplane()
        .pushPoints(dot_pts)
        .circle(1.4)
        .cutBlind(-p.constellation_relief_depth)
    )

    # ---- zenith collars at indices 0, 4, 7 (same shared ring, same list).
    # Added after the flat-face cuts above so they don't steal the ">Z"
    # selector; a resting mask disc stack still clears the well ring by
    # zenith_collar_h either way.
    for idx in p.zenith_indices:
        cx, cy = RING_XY[idx]
        drum = drum.union(_sunburst_collar(p, cx, cy))

    # ---- central axle post, added last for the same ">Z" selector reason.
    axle = (
        cq.Workplane("XY")
        .circle(p.axle_dia / 2.0)
        .extrude(p.axle_rise)
        .translate((0, 0, p.plinth_drum_h))
    )
    drum = drum.union(axle)

    return drum
