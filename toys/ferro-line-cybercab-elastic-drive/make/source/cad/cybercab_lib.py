"""Cybercab rubber-band toy: mm; rear at x=0, front +X, axle +Y.
Observed side ratios are in cybercab_spec.md; hidden interfaces are assumed.
"""
from build123d import *
from cadgen.assembly import AssemblyHelper
from elastic_lib import elastic
# Bundled exact cadfits helper supports both CAD launchers and direct measurements.
from cadfits import peg_for, slot_for
# [observed scaled] reference side dimensions; toy scale not prototype scale.
LENGTH=180.0
WIDTH=78.0
HEIGHT=60.0
REAR_X=34.0
FRONT_X=148.0
WHEEL_R=16.5
AXLE_Z=WHEEL_R
# [assumed] printable mechanism, low-power short winding trials.
WHEEL_T=7.0
TRACK=70.0
SHAFT_D=6.0
BORE_D=slot_for(SHAFT_D, 0.25)
FLOOR_Z=9.0
FLOOR_T=3.0
WALL=2.4
JOURNAL_Y=27.0
JOURNAL_W=5.0
JOURNAL_X=12.0
JOURNAL_TOP=22.0
SPOOL_R=4.2
SPOOL_W=9.0
HOOK_R=1.8
HOOK_REACH=5.0
BAND_ANCHOR_X=134.0
BODY_PROFILE=[(0,39),(3,40),(30,47),(45,52),(60,56),(82,59.5),(97,60),(110,58),(125,51),(140,42),(150,37),(175,29.5),(180,25),(180,9),(5,9)]
INNER_PROFILE=[(x,z-3.6) for x,z in BODY_PROFILE[:-2]]+[(180,-10),(0,-10)]
ARCH_R=18.5
RAIL_X=(71.0,108.0)
RAIL_Y=20.0
RAIL_LENGTH=2.4
RAIL_T=2.4
RAIL_Z=24.0
RAIL_RELEASE=4.0
GOLD=(0.67,0.53,0.31)
BLACK=(0.065,0.07,0.075)
WINDOW_PROFILE=[(54,41.7),(54,43.1),(83,55.8),(108,54.8),(134,41.4),(134,39.9)]
WINDOW_T=1.4
WINDOW_Y=38.3
# fixed geometry assumptions are tested in measure/check_spec.py
assert BORE_D>SHAFT_D and WALL>=2.4

def prism_xz(points, width):
    return extrude(Plane.XZ * Polygon(*points, align=None), amount=width/2, both=True)

def y_cylinder(r, length):
    return Cylinder(r,length, rotation=(90,0,0))

def complete_axle(driven=False):
    """One physical wheelset: shaft, tyres/discs and optional loose band finger."""
    part=y_cylinder(SHAFT_D/2,TRACK)
    for y in (-TRACK/2,TRACK/2):
        part += Pos(0,y,0)*y_cylinder(WHEEL_R,WHEEL_T)
        # Solid broad discs: no enclosed annular roof or trapped support.
    if driven:
        part+=y_cylinder(SPOOL_R,SPOOL_W)
        part+=Pos(SPOOL_R,0,0)*Cylinder(HOOK_R,HOOK_REACH, rotation=(0,90,0))
    return part.clean()

# Keyed, adhesive-secured end wheel: 0.25 mm per-face assembly clearance.
KEY_SIDE=3.4
KEY_SOCKET=slot_for(KEY_SIDE,0.25)
def axle_set(driven=False):
    part=complete_axle(driven) & (Pos(0,-20,0)*Box(40,102.6,40))
    part+=Pos(0,34,0)*Box(KEY_SIDE,6,KEY_SIDE)
    if driven:
        # Axle prints from the -Y wheel upward: taper supports the spool shoulder.
        part+=Pos(0,-5.1,0)*Cone(SHAFT_D/2,SPOOL_R,1.2,rotation=(-90,0,0))
        # Sloped rib carries the radial winding finger from below in print pose.
        rib=extrude(Polygon((1.7,-6.8),(6.7,-1.8),(6.7,0),(1.7,0),align=None),amount=1.8,both=True)
        part+=rib
    return part.clean()

def end_wheel():
    part=complete_axle(False) & (Pos(0,35,0)*Box(40,7,40))
    part-=Pos(0,33.7,0)*Box(KEY_SOCKET,7.2,KEY_SOCKET)
    return part.clean()

def end_wheel_print():
    return print_part(Rot(-90,0,0)*end_wheel())

def chassis(latch_deflection=0.0):
    part=Pos(LENGTH/2,0,FLOOR_Z+FLOOR_T/2)*Box(LENGTH-14,WIDTH-22,FLOOR_T)
    part-=Pos(74.75,0,FLOOR_Z)*Box(100.5,13,12)
    for x in (REAR_X,FRONT_X):
        for y in (-JOURNAL_Y,JOURNAL_Y):
            tower=Pos(x,y,(FLOOR_Z+JOURNAL_TOP)/2)*Box(JOURNAL_X,JOURNAL_W,JOURNAL_TOP-FLOOR_Z)
            bore=Pos(x,y,AXLE_Z)*y_cylinder(BORE_D/2,JOURNAL_W+2)
            mouth=Pos(x,y,(AXLE_Z+JOURNAL_TOP)/2)*Box(BORE_D,JOURNAL_W+2,JOURNAL_TOP-AXLE_Z+1)
            part+=tower-bore-mouth
    # Front band peg is broad-rooted; loop drops over it through open underside.
    part+=Pos(BAND_ANCHOR_X,0,(FLOOR_Z+AXLE_Z)/2)*Cylinder(3.0,AXLE_Z-FLOOR_Z)
    part+=Pos(BAND_ANCHOR_X,0,AXLE_Z)*Cylinder(4.4,2.4)
    # central captured slide rails; shell slides rearwards to release.
    for x in RAIL_X:
        for y in (-RAIL_Y,RAIL_Y):
            part+=Pos(x,y,(FLOOR_Z+RAIL_Z)/2)*Box(RAIL_LENGTH,RAIL_T,RAIL_Z-FLOOR_Z)
            part+=Pos(x,y,RAIL_Z)*Box(RAIL_LENGTH,7,RAIL_T)
    # Bed-rooted free beam: clearance slot isolates its flexible length.
    part-=Pos(92,13,10.5)*Box(38,8,3.2)
    # Tool-free thumb latch: XY bending keeps the beam load in the layer plane.
    part+=Pos(70.5,12,17)*Box(5,2.4,12)
    beam=extrude(Polygon((71,10.8),(73,10.8),(107,10.8-latch_deflection),(107,13.2-latch_deflection),(73,13.2),(71,13.2),align=None),amount=14)
    tooth=extrude(Polygon((104,12),(107,12),(107,15.2),(104,15.2),align=None),amount=14)
    part+=Pos(0,0,9)*beam
    part+=Pos(0,-latch_deflection,9)*tooth
    return part.clean()

def body():
    part=prism_xz(BODY_PROFILE,WIDTH)-prism_xz(INNER_PROFILE,WIDTH-2*WALL)
    # Open underside: service and support access, no trapped roof cavity.
    part-=Pos(LENGTH/2,0,-2)*Box(LENGTH+4,WIDTH-2*WALL,20)
    for x in (REAR_X,FRONT_X):
        for y in (-36,36):
            # Rear-pointed arch relieves the axial print overhang with 2 mm radial wheel clearance.
            arch=Pos(x,y,AXLE_Z)*y_cylinder(ARCH_R,13)
            arch+=Pos(0,y,0)*prism_xz([(x-40,-10),(x-40,9),(x-32,AXLE_Z),(x-13.1,AXLE_Z+13.1),(x-13.1,-10)],13)
            part-=arch & prism_xz([(px,pz-2.4) for px,pz in BODY_PROFILE[:-2]]+[(180,-10),(0,-10)],WIDTH+2)
    # Inner bearing caps extend from roof down to U-journal seating level.
    for x in (REAR_X,FRONT_X):
        for y in (-JOURNAL_Y,JOURNAL_Y):
            cap=Pos(x,y,39.15)*Box(JOURNAL_X,JOURNAL_W,33.7)
            cap-=Pos(x,y,AXLE_Z)*y_cylinder(BORE_D/2,JOURNAL_W+2)
            cap+=Pos(0,y,0)*prism_xz([(x+5,22.3),(x+6,22.3),(x+50,56),(x+5,56)],JOURNAL_W)
            part+=cap & prism_xz(BODY_PROFILE,WIDTH)
    # Connected rail sleeves: rearward slide unlocks their open-ended slots.
    for x in RAIL_X:
        for sign in (-1,1):
            y=sign*RAIL_Y
            sleeve=Pos(x,y,29)*Box(RAIL_LENGTH+WALL,12,18)
            slot=Pos(x-1,y,RAIL_Z)*Box(RAIL_LENGTH+WALL+3,7.6,RAIL_T+0.6)
            neck=Pos(x-1,y,RAIL_Z-5)*Box(RAIL_LENGTH+WALL+3,RAIL_T+0.6,10)
            sleeve=sleeve-slot-neck
            sleeve+=Pos(x-2.7,y,29)*Box(2.4,12,18)
            sleeve-=Pos(x-2.7,y,17)*Box(2.6,3,11)
            support=Pos(x,sign*28,34)*Box(RAIL_LENGTH+WALL,18,6)
            # Axial buttress rises toward the nose-down build plate.
            brace=Pos(0,y,0)*prism_xz([(x+1.4,20),(x+2.4,20),(x+55,60),(x+1.4,60)],12)
            brace=brace & prism_xz(BODY_PROFILE,WIDTH)
            brace-=Pos(x+8,y,10.5)*Box(20,7.6,30)
            part+=sleeve+support+brace
    part+=Pos(108.8,14.8,19.65)*Box(3,2.4,4.7)
    part+=(Pos(0,14.8,0)*prism_xz([(110,17.3),(110.3,17.3),(152,55),(110,55)],2.4)) & prism_xz(BODY_PROFILE,WIDTH)
    # Pocket clears the undeflected tooth in the seated state; striker catches on rearward slide.
    part-=Pos(105.4,14,20)*Box(3.8,4.6,6.6)
    for y in (-WINDOW_Y,WINDOW_Y):
        part-=Pos(0,y,0)*prism_xz(WINDOW_PROFILE,WINDOW_T+0.2)
    return part.clean()

def window():
    return prism_xz(WINDOW_PROFILE,WINDOW_T)

def window_print():
    return print_part(Rot(90,0,0)*window())

def print_part(part):
    bb=part.bounding_box()
    return Pos(0,0,-bb.min.Z)*part

def wheel_print(driven=False):
    return print_part(Rot(90,0,0)*axle_set(driven))

def assembly(angle=0.0, travel=0.0, body_shift=0.0, body_lift=0.0, latch_deflection=0.0):
    asm=AssemblyHelper('cybercab')
    pieces=[('chassis',chassis(latch_deflection),GOLD),('body',Pos(body_shift,0,body_lift)*body(),GOLD),
            ('rear_wheelset',Pos(REAR_X,0,AXLE_Z)*Rot(0,angle,0)*axle_set(True),BLACK),
            ('front_wheelset',Pos(FRONT_X,0,AXLE_Z)*Rot(0,angle,0)*axle_set(False),BLACK),
            ('rear_rightwheel',Pos(REAR_X,0,AXLE_Z)*Rot(0,angle,0)*end_wheel(),BLACK),
            ('front_rightwheel',Pos(FRONT_X,0,AXLE_Z)*Rot(0,angle,0)*end_wheel(),BLACK),
            ('left_window',Pos(body_shift,-WINDOW_Y,body_lift)*window(),BLACK),
            ('right_window',Pos(body_shift,WINDOW_Y,body_lift)*window(),BLACK),
            ('elastic',elastic(angle),(0.87,0.27,0.08))]
    for label,part,color in pieces:
        part=Pos(travel,0,0)*part
        part.color=Color(*color)
        asm.add(part,label,color=Color(*color))
    return asm.build()
