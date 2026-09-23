"""Twin logarithmic arms and integral dark annular field; paired journals."""
from functools import lru_cache
from math import sin,cos,exp,pi
from build123d import Wire,Face,Solid,Pos,Rot,Color
from params import *
from features.threads import cylinder,male_thread

@lru_cache(maxsize=None)
def post():
    straight=cylinder(POST_DIAMETER/2,POST_THREAD_START-CARRIER_THICKNESS,CARRIER_THICKNESS)
    screw=Pos(0,0,POST_THREAD_START)*male_thread(POST_DIAMETER/2,POST_THREAD_DEPTH,POST_THREAD_PITCH,POST_THREAD_LENGTH)
    seat=cylinder(HUB_RADIUS,STANDOFF,CARRIER_THICKNESS)
    return straight.fuse(screw,seat)

def ribbon():
    a=[];b=[]
    for i in range(121):
        t=SPIRAL_END*i/120;r=SPIRAL_R0*exp(SPIRAL_GROWTH*t)
        x=r*cos(t);y=r*sin(t)
        dx=SPIRAL_GROWTH*x-y;dy=SPIRAL_GROWTH*y+x
        length=(dx*dx+dy*dy)**.5
        nx=-dy/length*ARM_WIDTH/2;ny=dx/length*ARM_WIDTH/2
        a.append((x+nx,y+ny,0));b.append((x-nx,y-ny,0))
    return Solid.extrude(Face(Wire.make_polygon(a+b[::-1],close=True)),(0,0,CARRIER_THICKNESS))

@lru_cache(maxsize=None)
def carrier():
    from build123d import Box,Align
    base=cylinder(13,CARRIER_THICKNESS)-cylinder(MAIN_BORE/2,CARRIER_THICKNESS+2,-1)
    arm=ribbon()
    link=Pos(25,0,CARRIER_THICKNESS/2)*Box(32,ARM_WIDTH,CARRIER_THICKNESS)
    field=cylinder(CARRIER_FIELD_OD/2,CARRIER_THICKNESS)-cylinder(CARRIER_FIELD_ID/2,CARRIER_THICKNESS+2,-1)
    pieces=[field,arm,Rot(0,0,180)*arm,link,Rot(0,0,180)*link]
    for x,y in CENTERS:
        for s in (1,-1):
            pieces.extend([Pos(s*x,s*y,0)*cylinder(ARM_WIDTH/2,CARRIER_THICKNESS),Pos(s*x,s*y,0)*Rot(0,0,0 if s==1 else 180)*post()])
    for s in (1,-1):
        pieces.append(Pos(0,s*22,CARRIER_THICKNESS/2)*Box(ARM_WIDTH,26,CARRIER_THICKNESS))
        pillar=cylinder(BEZEL_PILLAR_OD/2,BEZEL_Z)
        pillar=pillar.fuse(cylinder(POST_DIAMETER/2,BEZEL_CAP_Z-BEZEL_Z,BEZEL_Z),Pos(0,0,BEZEL_CAP_Z)*male_thread(POST_DIAMETER/2,POST_THREAD_DEPTH,POST_THREAD_PITCH,CAP_HEIGHT))
        pieces.append(Pos(0,s*BEZEL_POST_RADIUS,0)*Rot(0,0,0 if s==1 else 180)*pillar)
    result=base.fuse(*pieces)
    result.color=Color(*BLACK)
    return result
