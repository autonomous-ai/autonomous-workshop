"""Removable roof closes the square guide and longitudinal-stop cavity."""
from build123d import Align, Box, Cone, Cylinder, Pos, Rot
import params as p


def build():
    cap = Pos(sum(p.LAUNCH_HOUSING_X) / 2, sum(p.LAUNCH_HOUSING_Y) / 2, (p.LAUNCH_GUIDE_TOP + p.LAUNCH_GUIDE_CAP_TOP) / 2) * Box(p.LAUNCH_HOUSING_X[1] - p.LAUNCH_HOUSING_X[0], p.LAUNCH_HOUSING_Y[1] - p.LAUNCH_HOUSING_Y[0], p.LAUNCH_GUIDE_CAP_TOP - p.LAUNCH_GUIDE_TOP)
    # Pocket front wall already closes this corner of the guide roof.
    cap -= Pos(sum(p.LAUNCH_POCKET_X) / 2, sum(p.LAUNCH_POCKET_Y) / 2, (p.LAUNCH_GUIDE_TOP + p.LAUNCH_GUIDE_CAP_TOP) / 2) * Box(p.LAUNCH_POCKET_X[1] - p.LAUNCH_POCKET_X[0], p.LAUNCH_POCKET_Y[1] - p.LAUNCH_POCKET_Y[0], p.LAUNCH_GUIDE_CAP_TOP - p.LAUNCH_GUIDE_TOP + 2 * p.LAUNCH_CUT_OVER)
    for x, y in p.LAUNCH_GUIDE_BOLTS:
        cap -= Pos(x, y, p.LAUNCH_GUIDE_TOP - p.LAUNCH_CUT_OVER) * Cylinder(p.M4_BORE / 2, p.LAUNCH_GUIDE_CAP_TOP - p.LAUNCH_GUIDE_TOP + 2 * p.LAUNCH_CUT_OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cap -= Pos(x, y, p.LAUNCH_GUIDE_CAP_TOP - p.LAUNCH_CSK_DEPTH) * Cone(p.M4_BORE / 2, p.CSK_RECESS_D / 2, p.LAUNCH_CSK_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return cap


def print_shape():
    shape = build()
    box = shape.bounding_box()
    return Pos(-box.min.X, -box.min.Y, -box.min.Z) * shape
