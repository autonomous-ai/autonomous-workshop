"""Small datum-explicit B-rep operations; no assembly ownership."""
from build123d import *
import params as p

def box_at(x0,x1,y0,y1,z0,z1):
    return Pos((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)*Box(x1-x0,y1-y0,z1-z0)

def axial_x(radius,x0,x1,y=0,z=0):
    return Pos((x0+x1)/2,y,z)*Rot(0,p.RIGHT_ANGLE,0)*Cylinder(radius,x1-x0)

def axial_y(radius,y0,y1,x=0,z=0):
    return Pos(x,(y0+y1)/2,z)*Rot(p.RIGHT_ANGLE,0,0)*Cylinder(radius,y1-y0)

def d_shaft(radius,flat,x0,x1):
    return axial_x(radius,x0,x1)-box_at(x0-p.CUT_EXTENSION,x1+p.CUT_EXTENSION,flat,radius+p.CUT_RADIAL_EXTENSION,-radius-p.CUT_EXTENSION,radius+p.CUT_EXTENSION)

def finish(shape,label,color):
    assert len(shape.solids()) == 1, f'{label}: disconnected solids'
    assert shape.is_valid and shape.volume > 0, label
    shape.label=label
    shape.color=Color(*color)
    return shape

def on_bed(shape,rotation=(0,0,0)):
    shape=Rot(*rotation)*shape
    shape=Pos(0,0,-shape.bounding_box().min.Z)*shape
    return shape
