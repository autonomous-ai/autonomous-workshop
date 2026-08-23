"""claim_crown -- low crenellated ring, 24mm OD x 3mm base, six 3mm teeth,
bore derived from the stool's own 16mm boss via seated_pair (CROWN_ID in
params.py). Drops onto an opponent stool boss; owner mark is 1-2 pierced
Ø3 holes through the flat top, which never changes the ring's own fit.
"""
import cadquery as cq

import params as p


def build_claim_crown(owner_holes):
    ring = (
        cq.Workplane("XY").circle(p.CROWN_OD / 2.0).circle(p.CROWN_ID / 2.0)
        .extrude(p.CROWN_T)
    )

    tooth_r_mid = (p.CROWN_OD / 2.0 + p.CROWN_ID / 2.0) / 2.0
    tooth_radial = (p.CROWN_OD - p.CROWN_ID) / 2.0
    tooth_tangential = 6.0
    tooth = cq.Workplane("XY").box(
        tooth_radial, tooth_tangential, p.CROWN_TOOTH_H, centered=(True, True, False)
    ).translate((tooth_r_mid, 0, p.CROWN_T))
    for i in range(p.CROWN_TOOTH_COUNT):
        ang = 360.0 * i / p.CROWN_TOOTH_COUNT
        ring = ring.union(tooth.rotate((0, 0, 0), (0, 0, 1), ang))

    hole_r = (p.CROWN_OD / 2.0 + p.CROWN_ID / 2.0) / 2.0
    hole = cq.Workplane("XY").circle(p.CROWN_HOLE_D / 2.0).extrude(p.CROWN_T + 0.4)
    hole = hole.translate((hole_r, 0, -0.2))
    for i in range(owner_holes):
        ang = 30.0 + 90.0 * i  # offset from the teeth (at 0/60/120...), one per quadrant
        ring = ring.cut(hole.rotate((0, 0, 0), (0, 0, 1), ang))

    return ring
