"""Open dark axle tunnel, passive translucent annulus, and knurled rotating grip."""
from functools import lru_cache
from math import pi,cos,sin
from build123d import Pos,Rot,Box,Align,Color,Cone
from params import *
from features.threads import cylinder,male_thread,female_tool

@lru_cache(maxsize=None)
def bezel():
    body=cylinder(BEZEL_OD/2,BEZEL_HEIGHT)-cylinder(BEZEL_ID/2,BEZEL_HEIGHT+2,-1)
    for sign in (-1,1):
        body=body.fuse(Pos(0,sign*BEZEL_POST_RADIUS,0)*cylinder(BEZEL_POST_OD/2,BEZEL_HEIGHT))
    #120 relief facets; all axial, no unsupported underside.
    cuts=[]
    for k in range(BEZEL_KNURL_COUNT):
        cut=Pos(BEZEL_OD/2+.15,0,BEZEL_HEIGHT/2)*Box(2*BEZEL_RELIEF,.65,BEZEL_HEIGHT+2)
        cuts.append(Rot(0,0,k*360/BEZEL_KNURL_COUNT)*cut)
    for s in (1,-1):
        cuts.append(Pos(0,s*BEZEL_POST_RADIUS,0)*cylinder(BEZEL_HOLE_DIAMETER/2,BEZEL_HEIGHT+2,-1))
    body=body.cut(*cuts);body.color=Color(*BLACK)
    return body

def d_tool(d,height,flat,z=0):
    return cylinder(d/2,height,z) & Pos(flat-d/2,0,z+height/2)*Box(d,2*d,height)

@lru_cache(maxsize=None)
def orange_disc():
    body=cylinder(ORANGE_OD/2,ORANGE_THICKNESS)-d_tool(ORANGE_ID,ORANGE_THICKNESS+2,8.3,-1)
    body.color=Color(*ORANGE)
    return body

def axle_thread(length):
    """Custom thread with tapered run-in/out; pitch and origin remain unchanged."""
    major=AXLE_OD/2; minor=major-MAIN_THREAD_DEPTH; h=AXLE_THREAD_LEAD
    envelope=Cone(minor,major,h,align=(Align.CENTER,Align.CENTER,Align.MIN))
    envelope=envelope.fuse(cylinder(major,length-2*h,h),Pos(0,0,length-h)*Cone(major,minor,h,align=(Align.CENTER,Align.CENTER,Align.MIN)))
    return male_thread(major,MAIN_THREAD_DEPTH,MAIN_THREAD_PITCH,length) & envelope

@lru_cache(maxsize=None)
def axle():
    length=AXLE_FRONT-AXLE_REAR
    maincap_start=MAIN_CAP_Z-AXLE_REAR
    body=cylinder(AXLE_OD/2,maincap_start-REAR_THREAD_LENGTH-THREAD_JOIN_OVERLAP/2,REAR_THREAD_LENGTH)
    rear=axle_thread(REAR_THREAD_LENGTH)
    body=body.fuse(rear)
    keycut=Pos(AXLE_KEY_FLAT+5,0,maincap_start/2)*Box(10,30,maincap_start+2)
    body=body-keycut
    # Wide tapered relief removes the coplanar seam without a horizontal overhang.
    h=AXLE_RUNOUT_HALF; z=REAR_THREAD_LENGTH; outer=AXLE_OD/2+.1
    retained=Pos(0,0,z-h)*Cone(outer,AXLE_RUNOUT_RADIUS,h,align=(Align.CENTER,Align.CENTER,Align.MIN))
    retained=retained.fuse(Pos(0,0,z)*Cone(AXLE_RUNOUT_RADIUS,outer,h,align=(Align.CENTER,Align.CENTER,Align.MIN)))
    relief=cylinder(outer+.1,2*h,z-h)-retained
    body=body-relief
    screw=Pos(0,0,maincap_start)*axle_thread(AXLE_FRONT-MAIN_CAP_Z)
    # Continuous flat lets keyed sun/orange pass the complete front thread.
    screw=screw-(Pos(AXLE_KEY_FLAT+5,0,length/2)*Box(10,30,length+2))
    shoulder_start=AXLE_SHOULDER_Z-AXLE_REAR
    ramp_height=AXLE_SHOULDER_OD/2-AXLE_KEY_FLAT+AXLE_RAMP_EXTRA
    ramp=Pos(0,0,shoulder_start-ramp_height)*Cone(AXLE_KEY_FLAT,AXLE_SHOULDER_OD/2,ramp_height,align=(Align.CENTER,Align.CENTER,Align.MIN))
    shoulder=cylinder(AXLE_SHOULDER_OD/2,AXLE_SHOULDER_THICKNESS,shoulder_start)
    bridge=cylinder(AXLE_OD/2-MAIN_THREAD_DEPTH,2*THREAD_JOIN_OVERLAP,maincap_start-THREAD_JOIN_OVERLAP)
    body=body.fuse(bridge,screw,ramp,shoulder)-cylinder(AXLE_ID/2,length+2,-1)
    body.color=Color(*BLACK)
    return body

@lru_cache(maxsize=None)
def main_cap():
    body=cylinder(MAIN_CAP_OD/2,MAIN_CAP_HEIGHT)-female_tool(AXLE_OD/2,MAIN_THREAD_DEPTH,MAIN_THREAD_PITCH,MAIN_CAP_HEIGHT,THREAD_CLEARANCE)
    body.color=Color(*BLACK)
    return body
