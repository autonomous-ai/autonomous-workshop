"""Rear annular frame, fixed cam walls, fixed pinion post, and base feet."""

from build123d import Pos, Rot
from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
from features.profiles import variable_cam_wall
import params as p


def build_frame():
    plate = cylinder_from(p.FRAME_R, p.FRAME_T) - cylinder_from(p.FRAME_R - p.FRAME_RING_W, p.FRAME_T)
    hub = cylinder_from(p.FRAME_HUB_R, p.FRAME_T) - cylinder_from(p.CARRIER_BORE / 2.0, p.FRAME_T)
    plate = plate + hub
    strut_length = p.FRAME_R - p.FRAME_RING_W - p.FRAME_HUB_R + 2.0 * p.FUSE_OVERLAP
    for angle in p.FRAME_STRUT_ANGLES:
        strut = box_from(
            p.FRAME_HUB_R - p.FUSE_OVERLAP, -p.FRAME_STRUT_W / 2.0, 0.0,
            strut_length, p.FRAME_STRUT_W, p.FRAME_T,
        )
        plate = plate + Rot(0.0, 0.0, angle) * strut
    for x in (-p.FRAME_TENON_X, p.FRAME_TENON_X):
        foot = box_from(
            x - p.FRAME_FOOT_W / 2.0,
            p.FRAME_FOOT_Y0,
            0.0,
            p.FRAME_FOOT_W, p.FRAME_FOOT_H, p.FRAME_T,
        )
        tenon = box_from(
            x - p.FRAME_TENON_W / 2.0,
            p.FRAME_TENON_Y0,
            0.0,
            p.FRAME_TENON_W, p.FRAME_TENON_H, p.FRAME_TENON_T,
        )
        slot = box_from(
            x - p.KEY_SLOT_W / 2.0,
            p.FRAME_KEY_LOCAL_Y - p.FRAME_KEY_SLOT_T / 2.0,
            -p.RUN_CLEAR,
            p.KEY_SLOT_W, p.KEY_SLOT_T, p.FRAME_T + 2.0 * p.RUN_CLEAR,
        )
        plate = plate + foot + tenon - slot
    axle_hole = cylinder_from(p.CARRIER_BORE / 2.0, p.FRAME_T)
    plate = plate - axle_hole
    for angle in p.BEZEL_PILOT_ANGLES:
        x, y = p.polar_xy(p.LIP_STANDOFF_R, angle)
        pilot_boss = cylinder_from(p.FRAME_PILOT_D / 2.0 + 2.0, p.FRAME_T, x=x, y=y)
        pilot_hole = cylinder_from(p.FRAME_PILOT_D / 2.0, p.FRAME_T, x=x, y=y)
        plate = plate + pilot_boss - pilot_hole
    inner_wall = Pos(0.0, 0.0, p.FRAME_T - p.FUSE_OVERLAP) * variable_cam_wall(True)
    outer_wall = Pos(0.0, 0.0, p.FRAME_T - p.FUSE_OVERLAP) * variable_cam_wall(False)
    pinion_boss = cylinder_from(
        p.PINION_FRAME_BORE / 2.0 + p.WALL,
        p.FRAME_T,
        x=p.PINION_X,
    )
    pinion_bore = cylinder_from(p.PINION_FRAME_BORE / 2.0, p.FRAME_T, x=p.PINION_X)
    result = plate + pinion_boss + inner_wall + outer_wall - pinion_bore
    return label_shape(result, "frame_cam")
