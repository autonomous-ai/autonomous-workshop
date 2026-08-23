"""pearl_one_ring / pearl_two_ring / pearl_three_ring: identical everywhere
but the raised ring count on the flat foot. A 16mm domed knob (11mm tall) on
a plain 6mm/16mm shaft. Local origin: bottom of shaft (the flat foot).
"""
import cadquery as cq

import params as p


def build_pearl(n_rings: int) -> cq.Workplane:
    shaft = (
        cq.Workplane("XY").circle(p.PEARL_SHAFT_D / 2.0)
        .extrude(p.PEARL_SHAFT_H)
    )
    knob = (
        cq.Workplane("XY", origin=(0, 0, p.PEARL_SHAFT_H))
        .circle(p.PEARL_KNOB_D / 2.0)
        .workplane(offset=p.PEARL_KNOB_H)
        .circle(1.0)
        .loft()
    )
    body = shaft.union(knob)

    # n_rings concentric raised rings on the flat foot (z=0, the only
    # marking on the piece) -- small, and only readable foot-up in a rack.
    foot_r = p.PEARL_SHAFT_D / 2.0
    for i in range(n_rings):
        r = foot_r - 0.8 - i * 1.0
        if r <= 0.3:
            continue
        ring = (
            cq.Workplane("XY").circle(r + 0.4).circle(r)
            .extrude(-p.PEARL_RING_H)
        )
        body = body.union(ring)
    return body
