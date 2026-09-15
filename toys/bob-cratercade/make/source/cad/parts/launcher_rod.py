"""One rigid square plunger, strike head, crosshead, stop lug and pull knob.

Bob repair: the plunger drops into uncovered guides along -Z. Its two enlarged
ends and integral closed-slot lug make a purely longitudinal insertion false.
"""
from build123d import Align, Box, Cone, Cylinder, Pos, Rot, fillet
import params as p


def build():
    shaft = Pos(p.LAUNCH_X, p.LAUNCH_ROD_REAR_Y + p.LAUNCH_ROD_LENGTH / 2, p.LAUNCH_ROD_Z) * Box(p.LAUNCH_ROD_SIDE, p.LAUNCH_ROD_LENGTH, p.LAUNCH_ROD_SIDE)
    head = Box(p.LAUNCH_HEAD_W, p.LAUNCH_HEAD_T, p.LAUNCH_HEAD_H)
    head = fillet(head.edges(), p.LAUNCH_EDGE_R)
    head = Pos(p.LAUNCH_X, p.LAUNCH_FACE_Y - p.LAUNCH_HEAD_T / 2, p.LAUNCH_ROD_Z) * head
    knob = Pos(p.LAUNCH_X, p.LAUNCH_ROD_REAR_Y - p.LAUNCH_KNOB_T / 2, p.LAUNCH_ROD_Z) * Rot(90, 0, 0) * Cylinder(p.LAUNCH_KNOB_R, p.LAUNCH_KNOB_T)
    cross = Pos(sum(p.LAUNCH_CROSS_X) / 2, sum(p.LAUNCH_CROSS_Y) / 2, sum(p.LAUNCH_CROSS_Z) / 2) * Box(p.LAUNCH_CROSS_X[1] - p.LAUNCH_CROSS_X[0], p.LAUNCH_CROSS_Y[1] - p.LAUNCH_CROSS_Y[0], p.LAUNCH_CROSS_Z[1] - p.LAUNCH_CROSS_Z[0])
    stem = Pos(p.LAUNCH_BAND_X, p.LAUNCH_MOVING_POST_Y, p.LAUNCH_CROSS_Z[0]) * Cylinder(p.LAUNCH_POST_R, p.LAUNCH_POST_TOP - p.LAUNCH_CROSS_Z[0], align=(Align.CENTER, Align.CENTER, Align.MIN))
    collar_top = p.LAUNCH_POST_TOP + p.LAUNCH_POST_HEAD_T
    collar_base = collar_top - p.LAUNCH_ROD_COLLAR_LAND
    collar = Pos(p.LAUNCH_BAND_X, p.LAUNCH_MOVING_POST_Y, collar_base) * Cylinder(p.LAUNCH_POST_HEAD_R, p.LAUNCH_ROD_COLLAR_LAND, align=(Align.CENTER, Align.CENTER, Align.MIN))
    collar += Pos(p.LAUNCH_BAND_X, p.LAUNCH_MOVING_POST_Y, collar_base - p.LAUNCH_ROD_COLLAR_RISE) * Cone(p.LAUNCH_POST_R, p.LAUNCH_POST_HEAD_R, p.LAUNCH_ROD_COLLAR_RISE, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lug = Pos(sum(p.LAUNCH_LUG_X) / 2, sum(p.LAUNCH_LUG_Y) / 2, sum(p.LAUNCH_LUG_Z) / 2) * Box(p.LAUNCH_LUG_X[1] - p.LAUNCH_LUG_X[0], p.LAUNCH_LUG_Y[1] - p.LAUNCH_LUG_Y[0], p.LAUNCH_LUG_Z[1] - p.LAUNCH_LUG_Z[0])
    shape = shaft + head + knob + cross + stem + collar + lug
    # A common flat underside at the shaft bottom prints every rigid branch
    # from the same bed plane. This trims only the lower knob/head lobes;
    # the strike plane, guide section, crosshead, post and hard stops stay put.
    bounds = shape.bounding_box()
    low = bounds.min.Z - p.LAUNCH_CUT_OVER
    bottom_cut = Pos((bounds.min.X + bounds.max.X) / 2, (bounds.min.Y + bounds.max.Y) / 2, (low + p.LAUNCH_ROD_PRINT_FLOOR) / 2) * Box(bounds.size.X + 2 * p.LAUNCH_CUT_OVER, bounds.size.Y + 2 * p.LAUNCH_CUT_OVER, p.LAUNCH_ROD_PRINT_FLOOR - low)
    return shape - bottom_cut


def print_shape():
    """Common flat underside on bed; sloped band collar grows self-supported."""
    shape = build()
    box = shape.bounding_box()
    return Pos(-box.min.X, -box.min.Y, -box.min.Z) * shape
