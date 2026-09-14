"""Smooth lower guide, including real root towers clear of launcher and bats."""
from math import hypot
from build123d import Face,Polyline,Pos,extrude,offset,Kind,Vector
import params as p
from features.primitives import z_cylinder,top_countersink

def mount_points(side):
    a,b,_=p.RETURN_GUIDE_POINTS[side]
    return tuple((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])) for t in p.RETURN_GUIDE_MOUNT_FRACTIONS)

def build(side="left"):
    points=p.RETURN_GUIDE_POINTS[side]
    path=Polyline(*points).wires()[0]
    corner=min(path.vertices(),key=lambda v:(v.center()-Vector(*points[1],0)).length)
    path=path.fillet_2d(p.RETURN_GUIDE_BEND_R,[corner])
    profile=offset(path,amount=p.RETURN_GUIDE_R,kind=Kind.ARC)
    body=extrude(Face(profile.wires()[0]),amount=p.PLAYFIELD_WALL_H)
    for x,y in mount_points(side):
        body+=z_cylinder(x,y,0,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ROOT_R)
        body-=z_cylinder(x,y,-p.PLAYFIELD_CUT_MARGIN,p.PLAYFIELD_WALL_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        body-=z_cylinder(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ACCESS_D/2)
        body-=top_countersink(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    assert len(body.solids())==1
    return body

def print_shape(side="left"):
    body=build(side)
    box=body.bounding_box()
    return Pos(-box.min.X,-box.min.Y,0)*body
