"""Flanged central axle with an annular groove for a printable snap clip."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_central_axle():
    axle = cylinder_from(p.CENTRAL_FLANGE_D / 2.0, p.CENTRAL_FLANGE_T)
    axle = axle + cylinder_from(p.CENTRAL_AXLE_D / 2.0, p.CENTRAL_AXLE_L, z=p.CENTRAL_FLANGE_T)
    groove = cylinder_from(p.CENTRAL_AXLE_D / 2.0, p.CLIP_GROOVE_W, z=p.CENTRAL_CLIP_Z0)
    groove = groove - cylinder_from(p.CENTRAL_GROOVE_CORE_D / 2.0, p.CLIP_GROOVE_W, z=p.CENTRAL_CLIP_Z0)
    return label_shape(axle - groove, "central_axle")
