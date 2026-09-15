"""Small named coordinate primitives; callers supply all dimensions."""
from build123d import Align, Box, Cylinder, Cone, Plane, Polygon, Pos, extrude

def bounded_box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1-x0, y1-y0, z1-z0,
                               align=(Align.MIN, Align.MIN, Align.MIN))

def yz_prism(x0, x1, points):
    face = Plane.YZ * Polygon(*points, align=None)
    return Pos(x0, 0, 0) * extrude(face, amount=x1-x0, dir=(1,0,0))

def x_cylinder(x0, length, radius, y=0, z=0):
    return Pos(x0, y, z) * Cylinder(radius, length, rotation=(0,90,0),
                                    align=(Align.CENTER,Align.CENTER,Align.MIN))

def z_cylinder(x, y, z0, length, radius):
    return Pos(x,y,z0) * Cylinder(radius,length,
                                 align=(Align.CENTER,Align.CENTER,Align.MIN))

def top_countersink(x,y,top_z,depth,bore_d,head_d):
    return Pos(x,y,top_z-depth)*Cone(bore_d/2,head_d/2,depth,
                                    align=(Align.CENTER,Align.CENTER,Align.MIN))
