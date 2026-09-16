"""Resolved static assembly from live component builders, millimetres.

The foot is the fixed root. World Z is the stand/slider/rotor axis. Tangent
root pins use Rx90 (local +Z -> minus tangent). The two named poses are
presentation geometry only: neither is a motion or insertion verification.
"""
import math
from build123d import Axis, Pos, Rot, Location, RigidJoint, LinearJoint, RevoluteJoint
from cadgen.assembly import AssemblyHelper
from params import *
from parts import support as fixed, drive, moving, chains
from parts.bell import bell
from features.common import at_polar


def occurrences(depression=0.0, cam_angle=0.0):
    """Leaf list with exact names used by the production inventory."""
    if not 0 <= depression <= STROKE:
        raise ValueError('static depression must be within the designed stroke')
    result = []
    def add(name, shape, pose=None, color=None):
        original_color = color or shape.color
        if pose is not None:
            shape = pose * shape
        shape.label, shape.color = name, original_color
        assert len(shape.solids()) == 1, name
        result.append((name, shape))
        return shape
    foot = add('support', fixed.support())
    RigidJoint('desk_datum', foot, Location((0,0,0)))
    add('anchor', fixed.anchor(), Pos(0,0,SUPPORT_ANCHOR_SEAT_Z)*Rot(0,0,SUPPORT_ANCHOR_LOCK_ANGLE))
    add('carrier', fixed.carrier())
    add('frame', fixed.frame())
    rotor_pose = Rot(0,0,cam_angle)
    cam = add('cam', drive.cam(), rotor_pose)
    RevoluteJoint('cam_axis', cam, Axis((0,0,ROTOR_TOP),(0,0,1)))
    add('cup', drive.cup(), rotor_pose)
    add('shaft', drive.shaft(), rotor_pose)
    add('drive_retainer', drive.drive_retainer(), rotor_pose)
    add('drive_thrust_washer', drive.drive_thrust_washer())
    lowered = Pos(0,0,-depression)
    slider = add('slider', moving.slider(), lowered)
    LinearJoint('stand_slide', slider, Axis((0,0,GUIDE_BOTTOM),(0,0,1)), linear_range=(-STROKE,0))
    add('keeper', moving.keeper(), lowered)
    # Pin heads seat on keeper top. Distal clips sit in the real necks.
    keeper_head_z = KEEPER_Z + KEEPER_H + KEEPER_PIN_HEAD_H
    for i,(radius,azimuth) in enumerate(moving.keeper_pin_datums(),1):
        pin_pose = lowered*at_polar(radius,azimuth,keeper_head_z)*Rot(0,0,azimuth)*Rot(180,0,0)
        add(f'keeper_pin_{i:02d}', moving.keeper_pin(), pin_pose)
        add(f'keeper_clip_{i:02d}', fixed.pivot_retainer(), pin_pose*Pos(0,0,KEEPER_PIN_GROOVE_Z))
    for i,azimuth in enumerate(RETURN_ANGLES,1):
        add(f'return_arm_{i:02d}', moving.return_arm(), lowered*at_polar(RETURN_R,azimuth)*Rot(0,0,azimuth))
    for i,azimuth in enumerate(RIBBON_ANGLES,1):
        pose = lowered*Rot(0,0,azimuth)*Pos(RIBBON_R-RIBBON_THICKNESS/2,0,RING_FLOOR_Z+RING_FLOOR_H)*Rot(0,0,90)*Rot(90,0,0)
        add(f'ribbon_{i:02d}', moving.ribbon(), pose, BLUSH if i%2 else MIST)
    root_angle = math.degrees(math.asin(depression/HORN_LENGTH))
    for i,azimuth in enumerate(range(0,360,45),1):
        pin_pose = Rot(0,0,azimuth)*Pos(PIVOT_R,FORK_INNER/2+FORK_WALL+PIVOT_PIN_HEAD_H,PIVOT_Z)*Rot(90,0,0)
        add(f'pivot_pin_{i:02d}', fixed.pivot_pin(), pin_pose)
        add(f'pivot_clip_{i:02d}', fixed.pivot_retainer(), pin_pose*Pos(0,0,SUPPORT_PIN_GROOVE_Z))
        # A depicted pose, not a dynamics solution: grade the bend across five
        # joints (at most 6.97deg per joint). A vertical first bead at full
        # depression would put its finite-width neck through the eye.
        link_angles = tuple(root_angle*max(0,4-j)/5 for j in range(CHAIN_COUNT))
        for j,shape in enumerate(chains.world_parts(azimuth,root_angle,link_angles)):
            name = f'chain_{i:02d}_root' if j==0 else f'chain_{i:02d}_bead_{j:02d}'
            add(name,shape,color=PEARL)
    for region in ('pearl','blush','mist'):
        add('bell_'+region,bell(region,print_orientation=False),lowered*Pos(0,0,BELL_SEATED_OFFSET_Z))
    return result


def assembly(depression=0.0, cam_angle=0.0):
    asm = AssemblyHelper('pearl_pulse')
    for name,shape in occurrences(depression,cam_angle):
        asm.add(shape,name)
    return asm.build()
