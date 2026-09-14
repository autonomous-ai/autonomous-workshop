"""Shared BREP construction, no product-specific dimensions."""
import validation  # Fail invalid package parameters before geometry.
from build123d import *

def box_bounds(bounds):
    x0,x1,y0,y1,z0,z1 = bounds
    return Pos(x0,y0,z0)*Box(x1-x0,y1-y0,z1-z0,align=(Align.MIN,Align.MIN,Align.MIN))

def prism_xz(points,y0,thickness):
    return Pos(0,y0,0)*extrude(Plane.XZ*Polygon(*points,align=None),amount=thickness,dir=(0,1,0))

def cylinder_y(radius,length,x,y,z):
    return Pos(x,y,z)*Rot(-90,0,0)*Cylinder(radius,length,align=(Align.CENTER,Align.CENTER,Align.MIN))

def annular_sector(x,z,inner,outer,start,end,y0,width):
    from math import cos,sin,radians
    def p(r,a): return (x+r*cos(radians(a)),z+r*sin(radians(a)))
    # Analytic arcs maintain smooth full fender profiles.
    with BuildLine(Plane.XZ) as boundary:
        CenterArc((x,z),outer,start,end-start)
        Line(p(outer,end),p(inner,end))
        CenterArc((x,z),inner,end,start-end)
        Line(p(inner,start),p(outer,start))
    return Pos(0,y0,0)*extrude(make_face(boundary.wires()),amount=width,dir=(0,1,0))

def plate_link(a,b,r,y0,width):
    from math import hypot
    dx,dz=b[0]-a[0],b[1]-a[1]
    length=hypot(dx,dz); nx,nz=-dz*r/length,dx*r/length
    p=prism_xz([(a[0]+nx,a[1]+nz),(a[0]-nx,a[1]-nz),(b[0]-nx,b[1]-nz),(b[0]+nx,b[1]+nz)],y0,width)
    return p.fuse(cylinder_y(r,width,*[a[0],y0,a[1]]),cylinder_y(r,width,*[b[0],y0,b[1]]))

def printed(shape,rotation=(90,0,0)):
    s=Rot(*rotation)*shape
    return Pos(0,0,-s.bounding_box().min.Z)*s

def colored(shape,rgb,label):
    assert len(shape.solids())==1, (label,len(shape.solids()))
    shape.label=label; shape.color=Color(*rgb)
    return shape
