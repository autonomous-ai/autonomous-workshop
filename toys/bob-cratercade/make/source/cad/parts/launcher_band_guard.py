"""Bolted cover over the replaceable band; open only with plunger unloaded."""
from build123d import Align, Box, Cone, Cylinder, Pos, Rot
import params as p


def build():
    roof = Pos(sum(p.LAUNCH_POCKET_X) / 2, sum(p.LAUNCH_POCKET_Y) / 2, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_GUARD_T / 2) * Box(p.LAUNCH_POCKET_X[1] - p.LAUNCH_POCKET_X[0], p.LAUNCH_POCKET_Y[1] - p.LAUNCH_POCKET_Y[0], p.LAUNCH_GUARD_T)
    # Removable downward apron closes the crosshead portal after insertion.
    roof += Pos(p.LAUNCH_POCKET_X[1] - p.LAUNCH_WALL / 2, sum(p.LAUNCH_TUNNEL_Y) / 2, (p.LAUNCH_TUNNEL_Z[1] + p.LAUNCH_GUARD_BOTTOM) / 2) * Box(p.LAUNCH_WALL, p.LAUNCH_TUNNEL_Y[1] - p.LAUNCH_TUNNEL_Y[0], p.LAUNCH_GUARD_BOTTOM - p.LAUNCH_TUNNEL_Z[1])
    for x, y in p.LAUNCH_GUARD_BOLTS:
        roof += Pos(x, y, p.LAUNCH_GUARD_BOTTOM) * Cylinder(p.LAUNCH_GUARD_COLUMN_R, p.LAUNCH_GUARD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        roof -= Pos(x, y, p.LAUNCH_GUARD_BOTTOM - p.LAUNCH_CUT_OVER) * Cylinder(p.M4_BORE / 2, p.LAUNCH_GUARD_T + 2 * p.LAUNCH_CUT_OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
        roof -= Pos(x, y, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_GUARD_T - p.LAUNCH_CSK_DEPTH) * Cone(p.M4_BORE / 2, p.CSK_RECESS_D / 2, p.LAUNCH_CSK_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Tangible tongue connects the south screw ear across its clear gap to roof.
    x, y = p.LAUNCH_GUARD_BOLTS[0]
    roof += Pos(x, (y + p.LAUNCH_POCKET_Y[0]) / 2, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_GUARD_T / 2) * Box(2 * p.LAUNCH_GUARD_COLUMN_R, p.LAUNCH_POCKET_Y[0] - y, p.LAUNCH_GUARD_T)
    roof -= Pos(x, y, p.LAUNCH_GUARD_BOTTOM - p.LAUNCH_CUT_OVER) * Cylinder(p.M4_BORE / 2, p.LAUNCH_GUARD_T + 2 * p.LAUNCH_CUT_OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
    roof -= Pos(x, y, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_GUARD_T - p.LAUNCH_CSK_DEPTH) * Cone(p.M4_BORE / 2, p.CSK_RECESS_D / 2, p.LAUNCH_CSK_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return roof


def print_shape():
    shape = Rot(180, 0, 0) * build()
    box = shape.bounding_box()
    return Pos(-box.min.X, -box.min.Y, -box.min.Z) * shape
