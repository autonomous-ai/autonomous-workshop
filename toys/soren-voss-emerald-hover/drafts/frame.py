"""Open frame: continuous sloped load paths, vertical guides and roofed bearings."""
from build123d import *
import math
import params as p
from features.primitives import box_at, axial_x, axial_y, finish

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

def frame():
    base=box_at(-35,35,-25,25,0,4)
    # Rounded plan corners, vertical edge treatment only.
    base=fillet(base.edges().filter_by(Axis.Z),radius=3)
    mast=box_at(-6.5,6.5,-25,-21,3.9,86)
    guides=[box_at(-6.5,6.5,-6.5,6.5,z,z+6) for z in (58,70)]
    braces=[yz_prism([(-21,z-22),(-21,z+6),(-6.5,z+6),(-6.5,z)],-6.5,6.5) for z in (58,70)]
    fan=loft([Pos(0,-19,67)*Rectangle(13,4),Pos(0,-16,80.1)*Rectangle(27.6,10)],ruled=True)
    bridge=box_at(-14.8,14.8,-17,-10.9,80,83.2)
    # Rear head access pockets leave a continuous rim and front boss face.
    bosses=[box_at(s*10-4.8,s*10+4.8,-17,-5,82.2,89.8) for s in (-1,1)]
    pedestal=loft([Pos(0,-14,83.1)*Rectangle(7,6),Pos(0,-13.5,85)*Rectangle(7,7)],ruled=True)+box_at(-3.5,3.5,-17,-10,84.9,88)
    towers=[box_at(s*22-2.5,s*22+2.5,-6,6,3.9,29) for s in (-1,1)]
    raw=base+[mast,*guides,*braces,fan,bridge,*bosses,pedestal,*towers]
    cuts=[box_at(-p.GUIDE_BORE/2,p.GUIDE_BORE/2,-p.GUIDE_BORE/2,p.GUIDE_BORE/2,57,77)]
    for s in (-1,1):
        cuts += [roof_x(p.SHAFT_BORE/2,s*22-3.5,s*22+3.5,0,p.SHAFT_Z),
                 roof_y(p.HINGE_FRAME_BORE/2,-18,-4,s*10,p.HINGE_Z)]
    raw=raw-cuts
    # Clearance for 6 mm shoulder pin heads; teardrop pocket opens at top.
    raw=raw-[roof_y(3.2,-26,-11,s*10,p.HINGE_Z) for s in (-1,1)]
    return finish(raw,'open_brass_frame',p.BRASS)
