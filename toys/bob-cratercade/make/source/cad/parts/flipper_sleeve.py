"""Replaceable 1.25-wall shoulder sleeve backed by the purchased M4 screw."""
from build123d import Align, Axis, Cylinder, Pos
import params as p


def sleeve():
    shape = Pos(0, 0, p.FLIPPER_SLEEVE_Z) * Cylinder(
        p.FLIPPER_SLEEVE_OD / 2, p.FLIPPER_SLEEVE_L,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape += Pos(0, 0, p.FLIPPER_SLEEVE_Z + p.FLIPPER_SLEEVE_L) * Cylinder(
        p.FLIPPER_FLANGE_D / 2, p.FLIPPER_FLANGE_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape -= Pos(0, 0, p.FLIPPER_SLEEVE_Z) * Cylinder(
        p.FLIPPER_SLEEVE_BORE / 2, p.FLIPPER_SLEEVE_L + p.FLIPPER_FLANGE_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape.label = "flipper_shoulder_sleeve"
    return shape


def print_sleeve():
    # Flange on bed, shoulder grows upward without a cantilevered flange.
    return Pos(0, 0, p.FLIPPER_SLEEVE_Z + p.FLIPPER_SLEEVE_L + p.FLIPPER_FLANGE_T) * sleeve().rotate(Axis.X, 180)
