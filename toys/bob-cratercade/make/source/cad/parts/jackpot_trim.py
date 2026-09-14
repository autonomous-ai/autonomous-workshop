"""Removable clamped trim block, centered on its fastening bore."""
from build123d import Align,Cone,Pos
import params as p
from features.primitives import bounded_box,z_cylinder

def build_trim():
    solid=bounded_box(-p.TRIM_W/2,p.TRIM_W/2,-p.TRIM_L/2,p.TRIM_L/2,
                       -p.TRIM_H/2,p.TRIM_H/2)
    bore=z_cylinder(0,0,-p.TRIM_H,p.TRIM_H*2,p.M4_BORE/2)
    head=Pos(0,0,-p.TRIM_H/2)*Cone(p.CSK_RECESS_D/2,p.M4_BORE/2,p.CSK_HEAD_MAX_H,
                                  align=(Align.CENTER,Align.CENTER,Align.MIN))
    return solid-bore-head
