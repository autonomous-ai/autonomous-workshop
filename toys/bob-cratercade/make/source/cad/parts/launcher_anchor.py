"""One relocatable band anchor; avoids overlapping collars at6mm pitch."""
from build123d import Align, Box, Cone, Cylinder, Pos
import params as p


def build():
    bottom = p.LAUNCH_POCKET_FLOOR
    top = bottom + p.LAUNCH_ANCHOR_T
    plate = Pos(0, p.LAUNCH_ANCHOR_PLATE_DY, bottom + p.LAUNCH_ANCHOR_T / 2) * Box(p.LAUNCH_ANCHOR_W, p.LAUNCH_ANCHOR_L, p.LAUNCH_ANCHOR_T)
    root = Pos(0, 0, bottom) * Cylinder(p.LAUNCH_POST_HEAD_R, p.LAUNCH_ANCHOR_ROOT_TOP - bottom, align=(Align.CENTER, Align.CENTER, Align.MIN))
    stem = Pos(0, 0, p.LAUNCH_ANCHOR_ROOT_TOP) * Cylinder(p.LAUNCH_POST_R, p.LAUNCH_POST_TOP - p.LAUNCH_ANCHOR_ROOT_TOP, align=(Align.CENTER, Align.CENTER, Align.MIN))
    collar = Pos(0, 0, p.LAUNCH_POST_TOP) * Cylinder(p.LAUNCH_POST_HEAD_R, p.LAUNCH_POST_HEAD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    anchor = plate + root + stem + collar
    anchor -= Pos(0, p.LAUNCH_ANCHOR_BOLT_OFFSET, bottom - p.LAUNCH_CUT_OVER) * Cylinder(p.M4_BORE / 2, p.LAUNCH_ANCHOR_T + 2 * p.LAUNCH_CUT_OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
    anchor -= Pos(0, p.LAUNCH_ANCHOR_BOLT_OFFSET, top - p.LAUNCH_CSK_DEPTH) * Cone(p.M4_BORE / 2, p.CSK_RECESS_D / 2, p.LAUNCH_CSK_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return anchor


def print_shape():
    shape = build()
    box = shape.bounding_box()
    return Pos(-box.min.X, -box.min.Y, -box.min.Z) * shape
