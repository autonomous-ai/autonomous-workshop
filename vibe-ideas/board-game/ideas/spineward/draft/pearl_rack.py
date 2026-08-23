"""pearl_rack: six round wells with a thumb scallop (a direct `cut_wells`
match), one end carrying a prism finial matching that seat's urchin_shell
knob shape -- a cosmetic identity match, not a mechanical mate.
"""
import cadquery as cq

import params as p
from blocks import cut_wells


def well_positions():
    x0 = -(p.RACK_N_WELLS - 1) * p.RACK_WELL_PITCH / 2.0
    return [(x0 + i * p.RACK_WELL_PITCH, 0.0, 0.0)
            for i in range(p.RACK_N_WELLS)]


def build_pearl_rack(n_flats: int) -> cq.Workplane:
    body = cq.Workplane("XY").box(
        p.RACK_L, p.RACK_W, p.RACK_H, centered=(True, True, False)
    )
    body = body.edges("|Z").fillet(3.0)

    body = cut_wells(body, well_positions(), p.RACK_WELL_D,
                      p.RACK_WELL_DEPTH, top_z=p.RACK_H, notch=True)

    finial = (
        cq.Workplane("XY")
        .polyline(p.polygon_pts(
            n_flats, p.RACK_FINIAL_VERTEX_R,
            rot_deg=p.face_forward_rot_deg(n_flats)))
        .close()
        .extrude(p.RACK_FINIAL_H)
    )
    finial = finial.edges("|Z").fillet(p.RACK_FINIAL_EDGE_FILLET)
    finial = finial.translate((p.RACK_L / 2.0 - 6.5, 0.0, p.RACK_H))
    body = body.union(finial)
    return body
