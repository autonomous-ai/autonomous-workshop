"""Reusable coordinate-plane prisms and supportable round-bearing roofs."""
from build123d import *
import math
from features.primitives import axial_x,axial_y

def yz_prism(points,x0,x1):
    return Pos(x0,0,0)*extrude(Plane.YZ*Polygon(*points,align=None),amount=x1-x0,dir=(1,0,0))

def xz_prism(points,y0,y1):
    return Pos(0,y0,0)*extrude(Plane.XZ*Polygon(*points,align=None),amount=y1-y0,dir=(0,1,0))

def roof_x(r,x0,x1,y,z):
    h=r/math.sqrt(2)
    return axial_x(r,x0,x1,y,z)+yz_prism([(y-h,z+h),(y+h,z+h),(y,z+r*math.sqrt(2))],x0,x1)

def roof_y(r,y0,y1,x,z):
    h=r/math.sqrt(2)
    return axial_y(r,y0,y1,x,z)+xz_prism([(x-h,z+h),(x+h,z+h),(x,z+r*math.sqrt(2))],y0,y1)

def rectangular_loft(sections):
    return loft([Pos(x,y,z)*Rectangle(w,d) for x,y,z,w,d in sections],ruled=True)
