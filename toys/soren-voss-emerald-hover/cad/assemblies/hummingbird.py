"""Datum-driven assembly. Rigid groups require the documented cured adhesive lands.

Coordinates: X span, +Y bill, +Z up. theta=0 is mid-travel; positive input
rotates about +X. Wings follow exact pin/slot and cam tangency constraints.
No generated STEP is imported as a design dependency.
"""
import math
from build123d import Pos, Rot, Axis, Location
from cadgen.assembly import AssemblyHelper
import params as p
from parts.frame import frame
from parts.drive import cam,shaft,crank
from parts.follower import yoke,rod,crosshead
from parts.pins import shoulder_pin,shoulder_cap,drive_pin,drive_cap
from parts.wings import wing
from parts.bird import bird_half
from validation import validate_parameters

GROUPS={
 'stationary':['frame','bird_left','bird_right','shoulder_pin_left','shoulder_pin_right','shoulder_cap_left','shoulder_cap_right'],
 'rotor':['shaft','cam_left','cam_right','crank'],
 'follower':['yoke','rod','crosshead'],
 'left_wing':['wing_left','drive_pin_left','drive_cap_left'],
 'right_wing':['wing_right','drive_pin_right','drive_cap_right'],
}

def pose(theta_deg=0):
    theta=math.radians(theta_deg)
    q=p.ECCENTRICITY*math.sin(theta)
    phi=math.degrees(math.asin(-q/p.INPUT_ARM))
    return q,phi

def placed_parts(theta_deg=0):
    validate_parameters()
    q,phi=pose(theta_deg)
    d={'frame':frame(),'bird_left':bird_half(-1),'bird_right':bird_half(1)}
    rotor_pose=Pos(0,0,p.SHAFT_Z)*Rot(theta_deg,0,0)
    d['shaft']=rotor_pose*shaft()
    d['crank']=rotor_pose*Pos(p.SHAFT_RIGHT-p.CRANK_SOCKET_DEPTH,0,0)*crank()
    for side,name in [(-1,'left'),(1,'right')]:
        d['cam_'+name]=rotor_pose*Pos(side*p.CAM_X[1],0,0)*cam()
        d['shoulder_pin_'+name]=Pos(side*p.HINGE_X,p.SHOULDER_PIN_Y,p.HINGE_Z)*shoulder_pin()
        d['shoulder_cap_'+name]=Pos(side*p.HINGE_X,p.SHOULDER_CAP_Y,p.HINGE_Z)*shoulder_cap()
        # Reflection belongs to the leaf; signed axis rotation gives matching lift.
        hinge=Pos(side*p.HINGE_X,0,p.HINGE_Z)*Rot(0,-side*phi,0)
        d['wing_'+name]=hinge*wing(side)
        d['drive_pin_'+name]=hinge*Pos(-side*p.INPUT_ARM,p.DRIVE_PIN_Y,0)*drive_pin()
        d['drive_cap_'+name]=hinge*Pos(-side*p.INPUT_ARM,p.DRIVE_CAP_Y,0)*drive_cap()
    d['yoke']=Pos(0,0,p.YOKE_CENTER_Z+q)*yoke()
    d['rod']=Pos(0,0,p.ROD_BASE_Z+q)*rod()
    d['crosshead']=Pos(0,0,p.CROSSHEAD_Z+q)*crosshead()
    for name,shape in d.items():
        shape.label=name
        assert len(shape.solids())==1 and shape.volume>0 and shape.is_valid,name
    return d

def build(theta_deg=0):
    leaves=placed_parts(theta_deg)
    asm=AssemblyHelper('emerald_hover')
    groups={name:asm.add_module(name,[leaves[k] for k in keys]) for name,keys in GROUPS.items()}
    # Explicit source datums; geometric pose is the solved closed-chain map above.
    asm.revolute_frame(groups['rotor'],'camshaft_axis',Axis((0,0,p.SHAFT_Z),(1,0,0)))
    asm.linear_frame(groups['follower'],'vertical_guide',Axis((0,0,0),(0,0,1)))
    for side,name in [(-1,'left'),(1,'right')]:
        asm.revolute_frame(groups[name+'_wing'],name+'_shoulder',Axis((side*p.HINGE_X,0,p.HINGE_Z),(0,1,0)))
    asm.rigid_frame(leaves['frame'],'bird_seat',Location(p.BIRD_SEAT_DATUM))
    return asm.build()
