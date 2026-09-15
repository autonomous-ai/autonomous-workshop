"""Arched deflector with actual R14 noses and open underside-access mounts."""
from math import cos,sin,radians
from build123d import CenterArc,Line,Wire,Face,Pos,extrude
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink

def nose(side):
    x=side*p.GUIDE_NOSE_X
    start,end=(30.0,90.0) if side>0 else (90.0,150.0)
    outer=p.GUIDE_NOSE_R+p.GUIDE_WALL_T/2
    inner=p.GUIDE_NOSE_R-p.GUIDE_WALL_T/2
    def point(r,a):
        return x+r*cos(radians(a)),p.GUIDE_NOSE_Y+r*sin(radians(a))
    wire=Wire([CenterArc((x,p.GUIDE_NOSE_Y),outer,start,end-start),Line(point(outer,end),point(inner,end)),
               CenterArc((x,p.GUIDE_NOSE_Y),inner,end,start-end),Line(point(inner,start),point(outer,start))])
    return extrude(Face(wire),amount=p.GUIDE_H)

def build():
    y=p.GUIDE_NOSE_Y+p.GUIDE_NOSE_R
    body=bounded_box(-p.GUIDE_L/2,p.GUIDE_L/2,y+p.GUIDE_WALL_T/2-p.GUIDE_BODY_W,y+p.GUIDE_WALL_T/2,0,p.PLAYFIELD_ROOT_T)
    body+=bounded_box(-p.GUIDE_NOSE_X,p.GUIDE_NOSE_X,y-p.GUIDE_WALL_T/2,y+p.GUIDE_WALL_T/2,0,p.GUIDE_H)
    body+=nose(-1)+nose(1)
    for x in (-p.MISSION_BOLT_PITCH/2,p.MISSION_BOLT_PITCH/2):
        body+=z_cylinder(x,p.GUIDE_BOLT_Y,0,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_ROOT_R)
        body-=z_cylinder(x,p.GUIDE_BOLT_Y,-p.PLAYFIELD_CUT_MARGIN,p.GUIDE_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        body-=top_countersink(x,p.GUIDE_BOLT_Y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    assert len(body.solids())==1
    return body
