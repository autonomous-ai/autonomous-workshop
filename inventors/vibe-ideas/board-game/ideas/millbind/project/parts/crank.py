"""crank_gear: the only power in the box. Full-height tooth barrel, then a
solid self-supporting riser that carries the cap/arm/knob up clear of a
neighbouring millstone's 48mm crown+hub envelope before it ever widens past
the barrel's own root radius, then the solid cap + a triangular arm gusset
(<=45deg outboard taper the whole way) up to a knurled knob, plus a raised
clockwise direction arrow -- the only piece with an arm, and the only piece
with a direction mark.

Repair (round 1): the cap/arm/knob used to sit directly on the barrel top
(z=30..55). A neighbouring millstone's crown (17mm radius, z30..36) and hub
(<=16mm radius, z36..48) share the same 30mm pin pitch as the crank -- and
idea.json's own DIRECTION rule names "a millstone meshing straight into the
crank" as an explicit legal position -- so the old cap (r=17.5) and the
knob's 28.9mm swept-arm radius both physically interpenetrated a meshed
millstone. The old arm was also a flat 3mm plate cantilevered into open air
over the cap, which needed print support. Both are fixed by the same
geometry change: `parts/crank.py` now carries the cap/arm/knob on a riser
that (a) stays at the barrel's own root_r while it passes through the
millstone's 30..48mm z-band -- comfortably inside the 30mm pin pitch against
the crown/hub radii above -- and only widens back out to the cap's full
outer_r once it is past that band, and (b) never steps outward faster than
45deg from vertical at any stage, so the whole structure is carried by solid
material below it and self-supports without print supports. See
params.py's crank_riser1_h/crank_riser2_h/crank_gusset_rise_h for the
numbers; crank_knob_d/crank_knob_standoff/crank_arm_offset/crank_cap_h
(idea.json's own knob figures, and this build's own unstated-in-spec arm
offset/cap thickness) are unchanged.
"""
from __future__ import annotations

import cadquery as cq

from params import Params
from parts.gears import build_barrel, bore_through


def make_crank_gear(p: Params) -> cq.Workplane:
    barrel = build_barrel(p, p.barrel_h, p.barrel_teeth_z0, p.barrel_teeth_z1)

    # Riser stage 1: a plain vertical-walled cylinder at the barrel's own
    # root_r, climbing from the barrel top (z=barrel_h) to 1mm above the
    # 48mm millstone envelope. Held at root_r (not outer_r) the whole way so
    # it clears a meshed millstone's crown/hub radii at the 30mm pin pitch
    # -- see validation.py's riser-vs-crown/hub clearance asserts.
    riser1_z0 = p.barrel_h
    riser1_z1 = riser1_z0 + p.crank_riser1_h
    riser1 = (
        cq.Workplane("XY")
        .circle(p.root_r)
        .extrude(p.crank_riser1_h)
        .translate((0, 0, riser1_z0))
    )

    # Riser stage 2: a cone widening root_r -> outer_r, entirely above the
    # millstone envelope so radius is no longer constrained by a neighbour
    # -- only by the <=45deg self-support taper (dx=5.625mm/dz=6mm).
    riser2_z1 = riser1_z1 + p.crank_riser2_h
    riser2 = (
        cq.Workplane("XY")
        .workplane(offset=riser1_z1)
        .circle(p.root_r)
        .workplane(offset=p.crank_riser2_h)
        .circle(p.outer_r)
        .loft()
    )

    cap = (
        cq.Workplane("XY")
        .circle(p.outer_r)
        .extrude(p.crank_cap_h)
        .translate((0, 0, riser2_z1))
    )
    cap_top = riser2_z1 + p.crank_cap_h

    # Solid triangular gusset: from the cap's own edge (outer_r, resting
    # flush on the cap below -- no overhang there) up to the knob's outer
    # edge, with the outboard face tapered <=45deg from vertical
    # (dx=10.5mm/dz=crank_gusset_rise_h) so every layer is carried by solid
    # material below it, per print_plan. The knob's whole footprint
    # (knob's inner edge at arm_offset - knob_d/2, i.e. inside the cap's own
    # radius, out to its outer edge) sits on this gusset's flat top face.
    knob_inner_x = p.crank_arm_offset - p.crank_knob_d / 2.0
    knob_outer_x = p.crank_arm_offset + p.crank_knob_d / 2.0
    gusset_profile = [
        (knob_inner_x, cap_top),
        (p.outer_r, cap_top),
        (knob_outer_x, cap_top + p.crank_gusset_rise_h),
        (knob_inner_x, cap_top + p.crank_gusset_rise_h),
    ]
    gusset = (
        cq.Workplane("XZ")
        .polyline(gusset_profile)
        .close()
        .extrude(p.crank_knob_d / 2.0, both=True)
    )

    knob_z0 = cap_top + p.crank_gusset_rise_h
    knob = (
        cq.Workplane("XY")
        .circle(p.crank_knob_d / 2.0)
        .extrude(p.crank_knob_standoff)
        .translate((p.crank_arm_offset, 0, knob_z0))
    )

    # Raised direction arrow on the cap, pointing tangentially (the clockwise
    # driving direction) -- the only piece in the game with a mark.
    arrow = (
        cq.Workplane("XY")
        .polyline([(-p.outer_r * 0.7, -4), (-p.outer_r * 0.7, 4), (-p.outer_r * 0.3, 0)])
        .close()
        .extrude(p.crank_arrow_relief)
        .translate((0, 0, cap_top))
    )

    body = (
        barrel.union(riser1).union(riser2).union(cap).union(gusset)
        .union(knob).union(arrow)
    )
    body = bore_through(p, body, p.barrel_h)
    return body
