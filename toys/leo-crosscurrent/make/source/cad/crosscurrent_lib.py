"""Crosscurrent parametric geometry. All sizes are designer assumptions in mm."""
from math import sin, cos, radians
from build123d import *
from cadgen.assembly import AssemblyHelper
# [assumed] Sized for six harbors, 20 mm nesting boats and a 220 mm bed.
BASE_R=105.0
BASE_H=4.0
INNER_R=42.0
OUTER_R=80.0
OUTER_IN_R=45.0
RING_H=5.0
RADIAL_CLEARANCE=0.5
GUIDE_H=2.0
GUIDE_W=1.8
INNER_GUIDE_W=1.5
INNER_BERTH_R=28.0
OUTER_BERTH_R=63.0
BERTH_R=11.1
BERTH_DEPTH=2.0
TOKEN_R=10.0
TOKEN_FOOT_R=8.2
TOKEN_CAVITY_R=8.6
TOKEN_FOOT_H=1.15
TOKEN_TAPER_H=2.025
TOKEN_H=5.2
TOKEN_FLOOR=3.0
ENGRAVE_DEPTH=0.5
TALLY_W=1.2
TALLY_L=5.0
TALLY_SPACING=2.3
SECTORS=6
STEP_DEG=360/SECTORS
SHORE_R=93.0
PIP_R=1.5
PIP_H=1.2
MARK_W=1.6
MARK_L=4.0
PIP_SPACING=4.2
ALIGNMENT_R=85.0
FINGER_R=12.0
FINGER_DEPTH=2.0
CUT_EXTRA=1.0
SHORE_REWARDS=(2,4,3,2,4,3)
# [inferred] Assembly datums from contacting surfaces, no artificial display gap.
RING_Z=BASE_H
BOAT_Z=BASE_H+RING_H-BERTH_DEPTH
STACK_PITCH=TOKEN_H-TOKEN_FOOT_H-TOKEN_TAPER_H*(TOKEN_CAVITY_R-TOKEN_FOOT_R)/(TOKEN_R-TOKEN_FOOT_R)
COLORS=['#e8ad49','#cf674c','#46899b','#745b95','#6c9369']
assert OUTER_IN_R-INNER_R > 2*RADIAL_CLEARANCE
assert TOKEN_CAVITY_R-TOKEN_FOOT_R >= 0.4-1e-8
assert TOKEN_R-TOKEN_CAVITY_R >= 1.2
assert TOKEN_FLOOR-ENGRAVE_DEPTH >= 1.2
assert INNER_BERTH_R+BERTH_R < INNER_R

def cylinder(radius,height):
    return Cylinder(radius,height,align=(Align.CENTER,Align.CENTER,Align.MIN))

def annulus(outer,inner,height):
    return cylinder(outer,height)-cylinder(inner,height)

def polar(radius,harbor,angle=0):
    a=radians(-harbor*STEP_DEG-angle)
    return (radius*cos(a),radius*sin(a))

def build_base():
    result=cylinder(BASE_R,BASE_H)
    # Low external guide holds the outer carrier laterally; both carriers lift out.
    result += Pos(0,0,BASE_H)*annulus(OUTER_R+RADIAL_CLEARANCE+GUIDE_W,OUTER_R+RADIAL_CLEARANCE,GUIDE_H)
    # Integral inner guide locates the inner disk without depending on outer ring.
    result += Pos(0,0,BASE_H)*annulus(INNER_R+RADIAL_CLEARANCE+INNER_GUIDE_W,INNER_R+RADIAL_CLEARANCE,GUIDE_H)
    for h,reward in enumerate(SHORE_REWARDS):
        x,y=polar(SHORE_R,h)
        # Raised reward pips, centered on the shore harbor.
        for k in range(reward):
            tangent=(k-(reward-1)/2)*PIP_SPACING
            a=radians(-h*STEP_DEG)
            result += Pos(x-sin(a)*tangent,y+cos(a)*tangent,BASE_H)*cylinder(PIP_R,PIP_H)
        x,y=polar(ALIGNMENT_R,h)
        result += Pos(x,y,BASE_H)*Rot(0,0,-h*STEP_DEG)*Box(MARK_L,MARK_W,PIP_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return result

def cut_berths(result,radius):
    for h in range(SECTORS):
        x,y=polar(radius,h)
        result -= Pos(x,y,RING_H-BERTH_DEPTH)*cylinder(BERTH_R,BERTH_DEPTH+CUT_EXTRA)
    return result

def build_inner():
    result=cut_berths(cylinder(INNER_R,RING_H),INNER_BERTH_R)
    # Deep central finger well permits gripping without touching the boats.
    result -= Pos(0,0,RING_H-FINGER_DEPTH)*cylinder(FINGER_R,FINGER_DEPTH+CUT_EXTRA)
    return result

def build_outer():
    return cut_berths(annulus(OUTER_R,OUTER_IN_R,RING_H),OUTER_BERTH_R)

def build_boat(identity):
    result=cylinder(TOKEN_FOOT_R,TOKEN_FOOT_H)
    result += Pos(0,0,TOKEN_FOOT_H)*Cone(TOKEN_FOOT_R,TOKEN_R,TOKEN_TAPER_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    result += Pos(0,0,TOKEN_FOOT_H+TOKEN_TAPER_H)*cylinder(TOKEN_R,TOKEN_H-TOKEN_FOOT_H-TOKEN_TAPER_H)
    result -= Pos(0,0,TOKEN_FLOOR)*cylinder(TOKEN_CAVITY_R,TOKEN_H)
    for k in range(identity):
        x=(k-(identity-1)/2)*TALLY_SPACING
        result -= Pos(x,0,TOKEN_FLOOR-ENGRAVE_DEPTH)*Box(TALLY_W,TALLY_L,ENGRAVE_DEPTH+CUT_EXTRA,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return result

# The two boats sharing a berth are deliberate: all occupants must travel.
DEMO_BOATS=((1,'a',0,0),(2,'b',0,0),(3,'a',1,3),(1,'b',1,3),(2,'a',0,2),(3,'b',1,1),(4,'a',0,4),(4,'b',1,4),(5,'a',0,5),(5,'b',1,2))

def assemble(angle_inner=0,angle_outer=0):
    asm=AssemblyHelper('crosscurrent')
    asm.add(build_base(),'shore',color=Color('#eee2c9'))
    asm.add(Pos(0,0,RING_Z)*Rot(0,0,-angle_inner)*build_inner(),'inner',color=Color('#e6ae48'))
    asm.add(Pos(0,0,RING_Z)*Rot(0,0,-angle_outer)*build_outer(),'outer',color=Color('#448da0'))
    stacks={}
    for identity,letter,ring,h in DEMO_BOATS:
        key=(ring,h)
        level=stacks.get(key,0)
        stacks[key]=level+1
        angle=angle_inner if ring==0 else angle_outer
        x,y=polar(INNER_BERTH_R if ring==0 else OUTER_BERTH_R,h,angle)
        # Nesting cone contacts cavity rim: measured pitch derives from taper.
        pitch=STACK_PITCH
        boat=Pos(x,y,BOAT_Z+level*pitch)*Rot(0,0,-angle)*build_boat(identity)
        asm.add(boat,f'boat_{identity}_{letter}',color=Color(COLORS[identity-1]))
    return asm.compound()
