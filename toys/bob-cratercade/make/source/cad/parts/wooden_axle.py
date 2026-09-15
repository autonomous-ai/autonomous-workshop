"""Ordinary cut 4 mm beech stock; nominal proxy after bounded catalog probe."""
import params as p
from features.primitives import x_cylinder

def build_axle():
    return x_cylinder(p.AXLE_X0,p.AXLE_LENGTH,p.AXLE_D/2)
