"""crank_gear: the only power in the box. Full-height barrel + solid cap +
offset arm/knob (gusset routed to self-support) + a raised direction arrow.
"""
import cadquery as cq

import params as p
from gears import build_barrel, bore_through


def build_crank_gear() -> cq.Workplane:
    barrel = build_barrel(p.BARREL_H, p.BARREL_TEETH_Z0, p.BARREL_TEETH_Z1)

    cap = (
        cq.Workplane("XY")
        .circle(p.OUTER_R)
        .extrude(p.CRANK_CAP_H)
        .translate((0, 0, p.BARREL_H))
    )

    # Solid gusset: barrel wall up to the knob base, built AS the cap's own
    # thickness so it self-supports (flat top-face layers only, per
    # print_plan) rather than a thin free bar bridging to an isolated knob.
    gusset_len = p.CRANK_ARM_OFFSET + p.CRANK_KNOB_D / 2.0
    gusset = (
        cq.Workplane("XY")
        .center(0, 0)
        .rect(gusset_len, p.CRANK_KNOB_D, centered=False)
        .extrude(p.CRANK_CAP_H)
        .translate((0, -p.CRANK_KNOB_D / 2.0, p.BARREL_H))
    )

    knob = (
        cq.Workplane("XY")
        .circle(p.CRANK_KNOB_D / 2.0)
        .extrude(p.CRANK_KNOB_STANDOFF)
        .translate((p.CRANK_ARM_OFFSET, 0, p.BARREL_H + p.CRANK_CAP_H))
    )

    # 1.2mm raised direction arrow on the cap, pointing clockwise (+Y at
    # the -X side of the cap, tangential) -- the only piece with a mark.
    arrow = (
        cq.Workplane("XY")
        .polyline([(-p.OUTER_R * 0.7, -4), (-p.OUTER_R * 0.7, 4), (-p.OUTER_R * 0.3, 0)])
        .close()
        .extrude(p.CRANK_ARROW_RELIEF)
        .translate((0, 0, p.BARREL_H + p.CRANK_CAP_H))
    )

    body = barrel.union(cap).union(gusset).union(knob).union(arrow)
    body = bore_through(body, p.BARREL_H)
    return body
