"""Stationary pivot thrust pedestal, clamped through deck by metal fastener."""
from build123d import Align, Cylinder
import params as p


def pedestal():
    shape = Cylinder(p.FLIPPER_PEDESTAL_R, p.FLIPPER_PEDESTAL_H,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape -= Cylinder(p.M4_BORE / 2, p.FLIPPER_PEDESTAL_H,
                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape.label = "flipper_pedestal"
    return shape
