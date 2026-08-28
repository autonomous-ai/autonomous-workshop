"""Broad shield-hub crank with integral 8 mm grip post."""

from build123d import Circle, Pos, Rot, extrude, make_hull
from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
import params as p


def build_crank_arm():
    hub_profile = Circle(p.CRANK_HUB_D / 2.0)
    grip_profile = Pos(p.CRANK_GRIP_X, 0.0) * Circle(p.CRANK_ARM_W / 2.0)
    lever_body = extrude(make_hull([hub_profile.edges(), grip_profile.edges()]), amount=p.CRANK_ARM_T)
    grip_post = cylinder_from(p.GRIP_POST_D / 2.0, p.GRIP_POST_L, z=p.CRANK_ARM_T, x=p.CRANK_GRIP_X)
    round_hole = cylinder_from(p.CRANK_HUB_BORE_D / 2.0, p.CRANK_ARM_T)
    d_window = box_from(
        -p.CRANK_HUB_BORE_D / 2.0, -p.CRANK_HUB_BORE_D / 2.0, 0.0,
        p.CRANK_HUB_BORE_D / 2.0 + p.D_FLAT_X + p.RUN_CLEAR, p.CRANK_HUB_BORE_D, p.CRANK_ARM_T,
    )
    d_hole = round_hole & d_window
    grip_groove = cylinder_from(
        p.GRIP_POST_D / 2.0, p.CLIP_GROOVE_W, z=p.GRIP_CLIP_Z0, x=p.CRANK_GRIP_X
    )
    grip_groove = grip_groove - cylinder_from(
        p.GRIP_GROOVE_CORE_D / 2.0, p.CLIP_GROOVE_W, z=p.GRIP_CLIP_Z0, x=p.CRANK_GRIP_X
    )
    lever = Rot(0.0, 0.0, p.CRANK_ARM_OFFSET_DEG) * (lever_body + grip_post - grip_groove)
    return label_shape(lever - d_hole, "crank_arm")
