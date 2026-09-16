"""Shared deterministic feature constructors; dimensions supplied by parts."""
import math
from build123d import *
def cylinder(r,h,z=0):
    return Pos(0,0,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))
def box(w,d,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))
def annulus(ro,ri,h,z=0):
    return cylinder(ro,h,z)-cylinder(ri,h+2,z-1)
def radial(shape,angle):
    return Rot(0,0,angle)*shape
def at_polar(radius,angle,z=0):
    a=math.radians(angle)
    return Pos(radius*math.cos(a),radius*math.sin(a),z)
def xz_prism(points,thickness):
    return extrude(Plane.XZ*Polygon(*points,align=None),amount=thickness,dir=(0,1,0)).translate((0,-thickness/2,0))
def fused(first,others):
    return first.fuse(*others).clean() if others else first

def bed(shape,invert=False):
    s=Rot(180,0,0)*shape if invert else shape
    return Pos(0,0,-s.bounding_box().min.Z)*s

def finish(shape,label,color):
    assert len(shape.solids())==1, (label,len(shape.solids()))
    shape.label=label
    shape.color=color
    return shape
