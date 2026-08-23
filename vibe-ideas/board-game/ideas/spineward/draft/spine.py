"""spine: a 6mm/12mm peg fully buried flush in a shell socket, topped by an
11mm-thick wedge quill standing 20mm proud. Local origin: bottom of peg.
"""
import cadquery as cq

import params as p


def build_spine() -> cq.Workplane:
    peg = (
        cq.Workplane("XY").circle(p.SPINE_PEG_D / 2.0)
        .extrude(p.SPINE_PEG_H)
    )
    bw, bt = p.SPINE_BLADE_BASE
    tw, tt = p.SPINE_BLADE_TIP
    blade = (
        cq.Workplane("XY", origin=(0, 0, p.SPINE_PEG_H))
        .rect(bw, bt).workplane(offset=p.SPINE_EXPOSED_H)
        .rect(tw, tt)
        .loft()
    )
    return peg.union(blade)
