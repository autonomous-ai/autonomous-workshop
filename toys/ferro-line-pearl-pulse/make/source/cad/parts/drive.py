"""Printable retained rubber-drive stack; dimensions are original design.

No dynamic proof is implied. The working cam plane is unchanged. Shaft, cam
and cup have explicit opposed axial stops with 0.2 mm total upward clearance.
"""
from build123d import *
from params import *
from features.common import *


def cam():
    # A tilted planar face is sinusoidal at constant working radius.
    # Root owns the finite follower/contact-offset reconciliation.
    bottom = ROTOR_TOP-CAM_MIN_THICKNESS-STROKE/2
    wedge = xz_prism([
        (-KEY_R,bottom-STROKE/2*KEY_R/CAM_TRACK_R),
        (KEY_R,bottom+STROKE/2*KEY_R/CAM_TRACK_R),
        (KEY_R,ROTOR_TOP),(-KEY_R,ROTOR_TOP)],2*KEY_R)
    low = ROTOR_TOP-STROKE-CAM_MIN_THICKNESS-2
    s = cylinder(ROTOR_R,ROTOR_TOP-low,low) & wedge
    # Raised central web receives the shaft's positive lower cross-shoulder.
    # It clears the fixed stem at z97; the working r14 track is unchanged.
    s -= cylinder(CAM_CENTER_CLEAR_R,DRIVE_CAM_WEB_BOTTOM-low,low)
    inner = ROTOR_R-1.0
    lugs = [box(KEY_R-inner,6.0,3.0,x=sign*(KEY_R+inner)/2,
                z=ROTOR_TOP-3) for sign in (-1,1)]
    s = fused(s,lugs)
    # Actual process-resolved underside arrows: CCW viewed from above means
    # clockwise viewed from beneath. The maximum-turn number remains in README.
    arrow = Pos(0,0,ROTOR_TOP-3-DRIVE_ARROW_H)*extrude(Polygon(
        (19.4,-2.0),(20.6,-2.0),(20.6,0.0),(21.4,0.0),
        (20.4,1.8),(19.6,1.8),(18.6,0.0),(19.4,0.0),align=None),
        amount=DRIVE_ARROW_H)
    s = fused(s,[arrow,Rot(0,0,180)*arrow])
    s -= box(CAM_COUPLING,CAM_COUPLING,ROTOR_TOP-low+1,z=low)
    return finish(s,'retained_face_cam_with_winding_arrows',LAVENDER)


def cup():
    s = annulus(CUP_OUTER_R,CAM_COUPLING/2,CUP_FLOOR_H,CUP_BOTTOM)
    s = fused(s,[
        # This outer rim is the stated upper axial stop against the stator's
        # cavity roof. At nominal pose its top is103.4, roof103.6.
        annulus(CUP_OUTER_R,CUP_OUTER_WALL_INNER,DRIVE_CUP_OUTER_WALL_H,
                CUP_BOTTOM+CUP_FLOOR_H),
        annulus(CUP_INNER_WALL_OUTER,CUP_INNER_WALL_INNER,CUP_WALL_H,
                CUP_BOTTOM+CUP_FLOOR_H)])
    s -= box(CAM_COUPLING,CAM_COUPLING,CUP_FLOOR_H+2,z=CUP_BOTTOM-1)
    return finish(s,'axially_retained_damping_grease_cup',LAVENDER)


def shaft():
    # Everything has the same Y=-1.6 broad-bed datum when laid on its side.
    s = box(AXLE_D,AXLE_D,DRIVE_JOURNAL_BOTTOM-DRIVE_LOWER_STEM_BOTTOM,
            z=DRIVE_LOWER_STEM_BOTTOM)
    # Closed lower ledge carries downward elastic tension. The right-side
    # loading mouth is ABOVE that ledge, so tension seats rather than ejects
    # the loop. All X/Z outlines share the common broad print face.
    hook = box(2*DRIVE_HOOK_OUTER_HALF_WIDTH,AXLE_D,
               DRIVE_HOOK_TOP-DRIVE_HOOK_BOTTOM,z=DRIVE_HOOK_BOTTOM)
    hook -= box(3.2,AXLE_D+2,
                DRIVE_HOOK_POCKET_TOP-DRIVE_HOOK_POCKET_BOTTOM,
                z=DRIVE_HOOK_POCKET_BOTTOM)
    hook -= box(2.0,AXLE_D+2,
                DRIVE_HOOK_MOUTH_TOP-DRIVE_HOOK_MOUTH_BOTTOM,
                x=2.4,z=DRIVE_HOOK_MOUTH_BOTTOM)
    shoulder = box(DRIVE_SHAFT_SHOULDER_WIDTH,AXLE_D,
        DRIVE_SHAFT_SHOULDER_TOP-DRIVE_SHAFT_SHOULDER_BOTTOM,
        z=DRIVE_SHAFT_SHOULDER_BOTTOM)
    # Small corner chamfers preserve full walls beside the cross-key slot.
    # Maximum corner radius2.126 fits the coordinated stator bore radius2.3.
    octagon = Polygon((-1.4,-1.6),(1.4,-1.6),(1.6,-1.4),(1.6,1.4),
        (1.4,1.6),(-1.4,1.6),(-1.6,1.4),(-1.6,-1.4),align=None)
    journal = Pos(0,0,DRIVE_JOURNAL_BOTTOM)*extrude(octagon,
        amount=DRIVE_SHAFT_HEAD_TOP-DRIVE_JOURNAL_BOTTOM)
    # Keep the complete upper end inside the journal envelope: the stator
    # must genuinely pass over it before the removable retainer is fitted.
    s = fused(s,[hook,shoulder,journal])
    # Through Y, so this passage is vertical in the broad-face print stance.
    s -= box(DRIVE_RETAINER_SLOT_WIDTH,AXLE_D+2,
        DRIVE_RETAINER_SLOT_TOP-DRIVE_RETAINER_SLOT_BOTTOM,
        z=DRIVE_RETAINER_SLOT_BOTTOM)
    return finish(s,'positive_retention_motor_shaft',LAVENDER)


def drive_retainer():
    """Flat printed split cross-key. World length along Y, thickness along X.

    Beam thickness1.0, gap0.8, and explicit0.4 mm barbs. The two fingers
    squeeze together for insertion/removal; release locks shoulders against
    the shaft head's +/-Y faces. Physical fatigue and insertion force unknown.
    """
    def yz(points):
        return extrude(Plane.YZ*Polygon(*points,align=None),
            amount=DRIVE_RETAINER_WIDTH,dir=(1,0,0)).translate(
                (-DRIVE_RETAINER_WIDTH/2,0,0))
    # Continuous bottom/top beams and solid finger-grip bridge at negative end.
    s = yz([(-5.2,106.2),(5.2,106.2),(5.2,109.0),(-5.2,109.0)])
    # Entry-side positive stops remain outside the passage, split by the gap.
    fixed_stop = yz([(-3.2,105.8),(-1.8,105.8),(-1.8,109.4),(-3.2,109.4)])
    # Exit-side barbs taper toward the insertion tips at positive Y.
    barb = yz([(1.8,105.8),(3.0,105.8),(3.5,106.2),(3.5,109.0),
               (3.0,109.4),(1.8,109.4)])
    s = fused(s,[fixed_stop,barb])
    s -= box(DRIVE_RETAINER_WIDTH+2,10.0,
             DRIVE_RETAINER_GAP_TOP-DRIVE_RETAINER_GAP_BOTTOM,
             y=1.0,z=DRIVE_RETAINER_GAP_BOTTOM)
    return finish(s,'removable_split_drive_cross_key',LAVENDER)


def drive_thrust_washer():
    """Removable washer under both cross-key ends; positive downward stop."""
    s = annulus(DRIVE_THRUST_WASHER_OUTER,DRIVE_THRUST_WASHER_INNER,
                DRIVE_THRUST_WASHER_H,DRIVE_THRUST_WASHER_BOTTOM)
    return finish(s,'drive_cross_key_thrust_washer',LAVENDER)
