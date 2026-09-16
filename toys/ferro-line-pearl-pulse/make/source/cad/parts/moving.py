"""Common sliding yoke and removable keeper, return arms and oral ribbons."""
import math
import cadfits
from build123d import *
from params import *
from features.common import *

def keeper_pin_datums():
    """Shared bore/assembly axes, staggered midway between horn sectors.

    The radial inset separates the holes from post notches; angular staggering
    keeps the supporting bosses clear of horn pins and return passages.
    """
    return tuple((21.0,a) for a in (22.5,157.5,292.5))

def slider():
    s=annulus(RING_OUTER_R,RING_INNER_R,RING_FLOOR_H,RING_FLOOR_Z)
    additions=[annulus(GUIDE_R,GUIDE_BORE/2,GUIDE_H,GUIDE_BOTTOM)]
    for a in RING_SPOKE_ANGLES:
        additions.append(radial(box(RING_OUTER_R,RING_SPOKE_W,RING_FLOOR_H,x=RING_OUTER_R/2,z=RING_FLOOR_Z),a))
    for a in BELL_POST_ANGLES:
        post=cylinder(RING_BELL_POST_D/2,RING_BELL_POST_TOP-RING_FLOOR_Z,RING_FLOOR_Z)
        head=xz_prism([(RING_POST_HEAD_INNER,RING_POST_HEAD_BOTTOM),(BELL_POST_R-RING_BELL_POST_D/2,RING_POST_RAMP_BOTTOM),(RING_POST_HEAD_OUTER,RING_POST_RAMP_BOTTOM),(RING_POST_HEAD_OUTER,RING_BELL_POST_TOP),(RING_POST_HEAD_INNER,RING_BELL_POST_TOP)],RING_POST_HEAD_TANGENT)
        additions.extend([at_polar(BELL_POST_R,a)*post,radial(head,a)])
    for r,a in keeper_pin_datums():
        additions.append(at_polar(r,a)*cylinder(KEEPER_BOSS_R,KEEPER_Z-RING_FLOOR_Z,RING_FLOOR_Z))
    for a in RIBBON_ANGLES:
        additions.append(radial(box(RIBBON_R+3.2,RIBBON_ROOT_WIDTH+1.6,RING_FLOOR_H,x=(RIBBON_R+3.2)/2,z=RING_FLOOR_Z),a))
    # Radial support for narrow follower, clear of rotating key/cam underside.
    additions += [box(CAM_TRACK_R+FOLLOWER_RADIAL/2,FOLLOWER_WIDTH+1.6,RING_FLOOR_H,x=(CAM_TRACK_R+FOLLOWER_RADIAL/2)/2,z=RING_FLOOR_Z),box(FOLLOWER_RADIAL,FOLLOWER_WIDTH,FOLLOWER_NOSE_Z-RING_FLOOR_Z,x=CAM_TRACK_R,z=RING_FLOOR_Z),Pos(CAM_TRACK_R,0,FOLLOWER_NOSE_Z)*Sphere(FOLLOWER_NOSE_R)]
    s=fused(s,additions)
    cuts=[cylinder(GUIDE_BORE/2,GUIDE_H+2,GUIDE_BOTTOM-1)]
    cuts.extend(at_polar(r,a)*cylinder(KEEPER_PILOT_D/2,KEEPER_Z-RING_FLOOR_Z+2,RING_FLOOR_Z-1) for r,a in keeper_pin_datums())
    cuts.extend(radial(box(RETURN_TAB_HOLE,RETURN_TAB_HOLE,RING_FLOOR_H+2,x=RETURN_R,z=RING_FLOOR_Z-1),a) for a in RETURN_ANGLES)
    cuts.extend(radial(box(RIBBON_THICKNESS+0.4,RIBBON_WIDTH+0.6,RING_FLOOR_H+2,x=RIBBON_R,z=RING_FLOOR_Z-1),a) for a in RIBBON_ANGLES)
    s=s.cut(*cuts)
    return finish(s,'sliding_horn_yoke_and_bell_posts',MIST)

def keeper():
    s=annulus(RING_OUTER_R,RING_INNER_R,KEEPER_H,KEEPER_Z)
    # Inboard bearing lands preserve 1.3mm around each Ø3mm clearance bore.
    s=fused(s,[at_polar(r,a)*cylinder(2.8,KEEPER_H,KEEPER_Z)
               for r,a in keeper_pin_datums()])
    # Ø2.4 post stems have 0.4mm radial clearance in these open edge notches.
    post_notch_r=cadfits.slot_for(RING_BELL_POST_D,0.4)/2
    cuts=[at_polar(BELL_POST_R,a)*cylinder(post_notch_r,KEEPER_H+2,KEEPER_Z-1) for a in BELL_POST_ANGLES]
    cuts += [at_polar(r,a)*cylinder(KEEPER_HOLE_D/2,KEEPER_H+2,KEEPER_Z-1) for r,a in keeper_pin_datums()]
    # Eight arm exits retain the inboard side of each horn pin.
    cuts += [radial(box(4.0,3.2,KEEPER_H+2,x=24.9,y=0.4,z=KEEPER_Z-1),a) for a in range(0,360,45)]
    # Open return-loop passages; the elastic legs cannot pass through a solid lid.
    cuts += [radial(box(3.2,4.8,KEEPER_H+2,x=24.8,z=KEEPER_Z-1),a) for a in RETURN_ANGLES]
    return finish(s.cut(*cuts),'removable_horn_ring_keeper',MIST)

def keeper_pin():
    # Positive distal C-clip retention; clearance pilot, no nominal interference.
    # Ø4mm bearing head clears the cam at the coordinated r21mm axes.
    s=cylinder(2.0,KEEPER_PIN_HEAD_H)
    additions=[cylinder(KEEPER_PIN_D/2,KEEPER_PIN_GROOVE_Z),
               cylinder(SUPPORT_PIN_NECK_R,SUPPORT_PIN_GROOVE_H,KEEPER_PIN_GROOVE_Z),
               Pos(0,0,KEEPER_PIN_GROOVE_Z+SUPPORT_PIN_GROOVE_H)*Cone(SUPPORT_PIN_NECK_R,SUPPORT_PIN_TIP_R,SUPPORT_PIN_TIP_R-SUPPORT_PIN_NECK_R,align=(Align.CENTER,Align.CENTER,Align.MIN)),
               # Thicken only the distal cap; groove/clip and cone datums stay.
               cylinder(SUPPORT_PIN_TIP_R,1.0,KEEPER_PIN_GROOVE_Z+SUPPORT_PIN_GROOVE_H+SUPPORT_PIN_TIP_R-SUPPORT_PIN_NECK_R)]
    return finish(fused(s,additions),'keeper_retention_pin',LAVENDER)

def return_arm():
    bottom=RETURN_MOVING_Z-2.2
    top=RING_FLOOR_Z+RING_FLOOR_H
    # Local X radial; planar arm prints on broad tangential face.
    s=box(RETURN_TAB_WIDTH,RETURN_TAB_WIDTH,top-bottom,z=bottom)
    # Lower eye land clears the carrier arc by0.2mm; upper retaining tab
    # keeps its full width above the yoke floor.
    s=fused(s,[box(RETURN_TAB_WIDTH+2.4,RETURN_TAB_WIDTH,RETURN_TAB_TOP_H,z=top),box(RETURN_TAB_WIDTH+2.0,RETURN_TAB_WIDTH,5.2,z=bottom)])
    s-=Pos(0,0,RETURN_MOVING_Z)*Rot(90,0,0)*Cylinder(0.9,RETURN_TAB_WIDTH+2)
    # Round loaded hole lips while retaining >1mm around the eye.
    eye_edges=[e for e in s.edges() if e.geom_type==GeomType.CIRCLE]
    if eye_edges:
        s=fillet(eye_edges,0.25)
    return finish(s,'removable_return_elastic_arm',MIST)

def ribbon():
    # Tangent/Z plane centred radially at0; crown-down top root datumz0.
    points=[]
    count=72
    for side,seq in ((1,range(count+1)),(-1,range(count,-1,-1))):
        for i in seq:
            length=RIBBON_LENGTH*i/count
            # Straight upper neck passes the 1.2mm yoke floor without
            # the sinusoid intruding into its 5.8mm-wide mounting slot.
            x=RIBBON_AMPLITUDE*math.sin(2*math.pi*max(0,length-2.4)/RIBBON_WAVELENGTH)
            points.append((x+side*RIBBON_WIDTH/2,-length))
    s=extrude(Polygon(*points,align=None),amount=RIBBON_THICKNESS,dir=(0,0,1))
    s=fused(s,[box(RIBBON_ROOT_WIDTH,RIBBON_ROOT_H,RIBBON_THICKNESS,y=RIBBON_ROOT_H/2,z=0)])
    return finish(s,'sinuous_oral_ribbon',BLUSH)
