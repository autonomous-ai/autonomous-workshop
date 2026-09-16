"""Fixed support, removable anchor and three-arm frame, in world datums."""
from build123d import *
from params import *
from features.common import *

def support():
    # Combined foot/stand removes a unnecessary thin-walled stem coupling.
    foot=cylinder(BASE_R,BASE_H)
    stem=cylinder(STAND_R,STAND_TOP)
    collar=Pos(0,0,SUPPORT_COLLAR_Z)*Cone(STAND_R,SUPPORT_COLLAR_R,SUPPORT_COLLAR_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    stand_key=radial(box(SUPPORT_KEY_OUTER_R-SUPPORT_KEY_ROOT_R,SUPPORT_KEY_WIDTH,SUPPORT_KEY_HEIGHT,x=(SUPPORT_KEY_OUTER_R+SUPPORT_KEY_ROOT_R)/2,z=CARRIER_Z),SUPPORT_KEY_ANGLE)
    s=fused(foot,[stem,collar,cylinder(SUPPORT_COLLAR_R,1.2,SUPPORT_COLLAR_Z+SUPPORT_COLLAR_H),stand_key])
    s-=cylinder(STAND_BORE_R,STAND_TOP+2,-1)
    s-=cylinder(ANCHOR_POCKET_R,ANCHOR_CAP_H+0.2)
    # Two limited bayonet tracks close at +45deg under positive motor reaction.
    tracks=[_arc_link((ANCHOR_CHANNEL_R+STAND_BORE_R)/2,ANCHOR_CHANNEL_R-STAND_BORE_R,a,a+SUPPORT_ANCHOR_LOCK_ANGLE,ANCHOR_LUG_BOTTOM,ANCHOR_LUG_H+0.4) for a in (0,180)]
    end=radial(box(2*ANCHOR_CHANNEL_R,ANCHOR_LUG_W,ANCHOR_LUG_H+0.4,z=ANCHOR_LUG_BOTTOM),SUPPORT_ANCHOR_LOCK_ANGLE)
    end=end & cylinder(ANCHOR_CHANNEL_R,ANCHOR_LUG_H+0.4,ANCHOR_LUG_BOTTOM)
    s=s.cut(*tracks,end)
    slots=[radial(box(2*ANCHOR_CHANNEL_R,ANCHOR_LUG_W+0.6,ANCHOR_LUG_BOTTOM+ANCHOR_LUG_H+0.4),a) for a in (0,180)]
    s=s.cut(*slots)
    return finish(s,'pearl_foot_and_hollow_stand',PEARL)

def anchor():
    s=fused(cylinder(ANCHOR_CAP_R,ANCHOR_CAP_H),[
        cylinder(ANCHOR_PEG_R,ANCHOR_PEG_H),
        box(2*ANCHOR_LUG_R,ANCHOR_LUG_W,ANCHOR_LUG_H,z=ANCHOR_LUG_BOTTOM)])
    hook=Pos(0,0,ANCHOR_PEG_H+ANCHOR_HOOK_R-0.8)*Rot(90,0,0)*annulus(ANCHOR_HOOK_R,ANCHOR_HOOK_INNER,ANCHOR_HOOK_THICKNESS)
    hook=hook-box(ANCHOR_HOOK_R,2*ANCHOR_HOOK_THICKNESS,ANCHOR_HOOK_R,x=ANCHOR_HOOK_R/2,z=ANCHOR_PEG_H+ANCHOR_HOOK_R)
    s=fused(s,[hook])
    return finish(s,'removable_motor_anchor',LAVENDER)

def _arc_link(r, width, a0, a1, z, height):
    if abs(a1-a0)<1e-8:
        return at_polar(r,a0)*cylinder(width/2,height,z)
    lo,hi=sorted((a0,a1))
    def xy(radius,a):
        return (radius*math.cos(math.radians(a)),radius*math.sin(math.radians(a)))
    ri,ro=r-width/2,r+width/2
    wire=Wire([CenterArc((0,0),ro,lo,hi-lo),
               Line(xy(ro,hi),xy(ri,hi)),
               CenterArc((0,0),ri,hi,lo-hi),
               Line(xy(ri,lo),xy(ro,lo))])
    return Pos(0,0,z)*extrude(Face(wire),amount=height)

def carrier():
    s=annulus(CARRIER_HUB_R,GUIDE_BORE/2,SUPPORT_STOP_Z-CARRIER_Z,CARRIER_Z)
    additions=[]
    holes=[]
    for inner,outer in zip(SUPPORT_INNER_ARM_ANGLES,COLUMN_ANGLES):
        additions += [radial(box(SUPPORT_ROUTE_R,CARRIER_ARM_W,CARRIER_H,x=SUPPORT_ROUTE_R/2,z=CARRIER_Z),inner),
                      _arc_link(SUPPORT_ROUTE_R,CARRIER_ARM_W,inner,outer,CARRIER_Z,CARRIER_H),
                      radial(box(COLUMN_R-SUPPORT_ROUTE_R+0.8,CARRIER_ARM_W,CARRIER_H,x=(COLUMN_R+SUPPORT_ROUTE_R)/2-0.4,z=CARRIER_Z),outer),
                      at_polar(COLUMN_R,outer)*cylinder(CARRIER_SOCKET_R,2*CARRIER_H,CARRIER_Z)]
        holes += [at_polar(COLUMN_R,outer)*box(COLUMN_SOCKET,COLUMN_SOCKET,2*CARRIER_H,z=CARRIER_Z+SUPPORT_SOCKET_FLOOR)]
    s=fused(s,additions).cut(*holes)
    s-=cylinder(GUIDE_BORE/2,SUPPORT_STOP_Z-CARRIER_Z+2,CARRIER_Z-1)
    keyslot=box(SUPPORT_KEY_SLOT_OUTER,SUPPORT_KEY_SLOT_WIDTH,SUPPORT_STOP_Z-CARRIER_Z+2,x=SUPPORT_KEY_SLOT_OUTER/2,z=CARRIER_Z-1)
    s-=radial(keyslot,SUPPORT_KEY_ANGLE)
    return finish(s,'fixed_lower_carrier',PEARL)

def frame():
    # Broad upper pads sit on bed in inverted print stance; forks grow upward.
    s=cylinder(STATOR_OUTER_R,FRAME_TOP-STATOR_LABYRINTH_BOTTOM,STATOR_LABYRINTH_BOTTOM)
    additions=[]
    for a in range(0,360,45):
        additions += [radial(box(PIVOT_R,FRAME_ARM_W,FRAME_H,x=PIVOT_R/2,z=FRAME_TOP-FRAME_H),a),at_polar(PIVOT_R,a)*cylinder(FORK_RADIUS+0.2,FRAME_H,FRAME_TOP-FRAME_H)]
        for sign in (-1,1):
            inner_r=PIVOT_R-FORK_RADIUS
            cheek_bottom=FORK_BOTTOM
            if (a,sign) in ((135,1),(270,-1)):
                # The nearby bell clearance reachesR27.384 in this fork frame.
                # Open relief removes its knife crescent and the thin web where
                # that crescent met the diamond journal, keeping the pin axis.
                inner_r=27.6
                cheek_bottom=85.7  # full wall below the45deg relieved ceiling
            outer_r=PIVOT_R+FORK_RADIUS
            additions += [radial(box(outer_r-inner_r,FORK_WALL,FRAME_TOP-cheek_bottom,x=(outer_r+inner_r)/2,y=sign*(FORK_INNER+FORK_WALL)/2,z=cheek_bottom),a)]
    for a in COLUMN_ANGLES:
        additions += [radial(box(COLUMN_R,FRAME_ARM_W,FRAME_H,x=COLUMN_R/2,z=FRAME_TOP-FRAME_H),a),at_polar(COLUMN_R,a)*box(COLUMN_WIDTH,COLUMN_WIDTH,FRAME_TOP-FRAME_POST_BOTTOM,z=FRAME_POST_BOTTOM)]
    # Annular return-anchor bridge, with three clearance windows for bell posts.
    additions += [annulus(SUPPORT_BRIDGE_OUTER,SUPPORT_BRIDGE_INNER,FRAME_H,FRAME_TOP-FRAME_H)]
    s=fused(s,additions)
    # Coordinated shaft journal: Ø4.6, bossØ7.2, inner cup wallR4.0..5.2.
    # R5.6 cavity keeps0.4 radial clearance around that revised cup wall.
    cuts=[cylinder(2.3,FRAME_TOP-STATOR_LABYRINTH_BOTTOM+2,STATOR_LABYRINTH_BOTTOM-1),annulus(STATOR_CAVITY_OUTER,STATOR_CAVITY_INNER,STATOR_CAVITY_TOP-STATOR_LABYRINTH_BOTTOM,STATOR_LABYRINTH_BOTTOM),annulus(STATOR_CAVITY_INNER,5.6,STATOR_FACE_Z-STATOR_LABYRINTH_BOTTOM,STATOR_LABYRINTH_BOTTOM),annulus(5.6,3.6,STATOR_CAVITY_TOP-STATOR_LABYRINTH_BOTTOM,STATOR_LABYRINTH_BOTTOM)]
    # The journal boss must clear the rotating cup's solid floor as well as
    # its inner wall:0.4mm nominal axial gap,0.2mm at maximum rotor end float.
    boss_bottom = CUP_BOTTOM + CUP_FLOOR_H + 0.4
    cuts.append(cylinder(3.6,boss_bottom-STATOR_LABYRINTH_BOTTOM,STATOR_LABYRINTH_BOTTOM))
    for a in range(0,360,45):
        diamond=Plane.XZ*Polygon((-PIVOT_BORE*0.67,0),(0,-PIVOT_BORE*0.94),(PIVOT_BORE*0.67,0),(0,PIVOT_BORE*0.94),align=None)
        if a in (135,270):
            # Keep a closed journal in the opposite cheek. The relieved cheek
            # gets a broad U mouth, eliminating both diamond's knife lips.
            relieved_sign=1 if a==135 else -1
            depth=FORK_WALL+0.4
            other_y=-relieved_sign*(FORK_INNER+FORK_WALL)/2
            bore=extrude(diamond,amount=depth,dir=(0,1,0)).translate((PIVOT_R,other_y-depth/2,PIVOT_Z))
            cuts.append(radial(bore,a))
            relieved_y=relieved_sign*(FORK_INNER+FORK_WALL)/2
            circular_end=extrude(Plane.XZ*Circle(PIVOT_BORE/2),amount=depth,dir=(0,1,0)).translate((PIVOT_R,relieved_y-depth/2,PIVOT_Z))
            journal_r=PIVOT_BORE/2
            left=PIVOT_R-FORK_RADIUS
            tangent_x=PIVOT_R+journal_r/math.sqrt(2)
            tangent_z=PIVOT_Z-journal_r/math.sqrt(2)
            left_floor=PIVOT_Z-journal_r*math.sqrt(2)+left-PIVOT_R
            #45deg line tangent to the lower circle: no flat inverted ceiling.
            mouth_profile=Plane.XZ*Polygon((left,left_floor),(tangent_x,tangent_z),(tangent_x,PIVOT_Z+journal_r),(left,PIVOT_Z+journal_r),align=None)
            mouth=extrude(mouth_profile,amount=depth,dir=(0,1,0)).translate((0,relieved_y-depth/2,0))
            cuts.append(radial(circular_end.fuse(mouth),a))
        else:
            # Diamond roof avoids unsupported horizontal bore ceiling.
            bore=extrude(diamond,amount=FORK_INNER+2*FORK_WALL+2,dir=(0,1,0)).translate((PIVOT_R,-(FORK_INNER+2*FORK_WALL+2)/2,PIVOT_Z))
            cuts.append(radial(bore,a))
    for a in BELL_POST_ANGLES:
        # Post clearance continues through nearby fork cheeks: stopping at the
        # plate underside left unsupported ledges at printZ3 and a moving clash.
        cuts.append(at_polar(BELL_POST_R,a)*cylinder(2.3,FRAME_TOP-FRAME_POST_BOTTOM+2,FRAME_POST_BOTTOM-1))
    for a in RETURN_ANGLES:
        # Closed rounded-end slot: thread a bight and girth-hitch the inner land.
        slot=Pos(RETURN_R,0,FRAME_TOP-FRAME_H-1)*extrude(SlotOverall(SUPPORT_RETURN_SLOT_LENGTH,SUPPORT_RETURN_SLOT_WIDTH),amount=FRAME_H+2)
        cuts.append(radial(slot,a))
    s=s.cut(*cuts)
    lips=[]
    for e in s.edges():
        bb=e.bounding_box()
        if bb.size.Z<1e-6 and (abs(bb.min.Z-FRAME_TOP)<1e-6 or abs(bb.min.Z-(FRAME_TOP-FRAME_H))<1e-6):
            c=e.center()
            if any(math.hypot(c.X-RETURN_R*math.cos(math.radians(a)),c.Y-RETURN_R*math.sin(math.radians(a)))<2.0 for a in RETURN_ANGLES):
                lips.append(e)
    if lips:
        s=fillet(lips,SUPPORT_RETURN_LIP_RADIUS)
    return finish(s,'fixed_pivot_frame_and_stator',PEARL)

def pivot_pin():
    # Distal mushroom passes the diamond fork; the removable C-clip captures it.
    s=cylinder(PIVOT_PIN_HEAD_R,PIVOT_PIN_HEAD_H)
    additions=[cylinder(PIVOT_D/2,SUPPORT_PIN_GROOVE_Z),
               cylinder(SUPPORT_PIN_NECK_R,SUPPORT_PIN_GROOVE_H,SUPPORT_PIN_GROOVE_Z),
               Pos(0,0,SUPPORT_PIN_GROOVE_Z+SUPPORT_PIN_GROOVE_H)*Cone(SUPPORT_PIN_NECK_R,SUPPORT_PIN_TIP_R,SUPPORT_PIN_TIP_R-SUPPORT_PIN_NECK_R,align=(Align.CENTER,Align.CENTER,Align.MIN)),
               cylinder(SUPPORT_PIN_TIP_R,1.2,SUPPORT_PIN_GROOVE_Z+SUPPORT_PIN_GROOVE_H+SUPPORT_PIN_TIP_R-SUPPORT_PIN_NECK_R)]
    return finish(fused(s,additions),'tangent_pivot_pin',LAVENDER)

def pivot_retainer():
    # Long flat spring arms open by0.05mm each over the Ø1.6 shaft neck.
    s=box(5.6,7.0,SUPPORT_PIN_CLIP_H,y=0.5)
    groove=cylinder(SUPPORT_PIN_CLIP_BORE/2,SUPPORT_PIN_CLIP_H+2,-1)
    entry=box(SUPPORT_PIN_CLIP_THROAT,5.0,SUPPORT_PIN_CLIP_H+2,y=2.5,z=-1)
    # Transition to the neck seat is rounded by the circular seat itself.
    s=s-groove-entry
    return finish(s,'removable_flat_pivot_C_clip',LAVENDER)
