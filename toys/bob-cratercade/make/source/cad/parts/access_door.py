"""Two captive access doors. Local U inward, V rearward, Z deck-normal.

Receiver fixed at original cell datum. Moving frame/cap/PET closed at +8 Z.
Root owns board transforms and occurrence labels; these builders return solids.
"""
import math
from build123d import Align, Axis, Cylinder, Plane, Polygon, Pos, Rot, extrude
from parts import canopy_frame, canopy_cap, canopy_sheet
from features.primitives import bounded_box as box, z_cylinder, top_countersink
import params as p

HINGE_V = (32.0, 112.0)
LATCH_V = (30.0, 114.0)
HINGE_U, HINGE_Z, OPEN_ANGLE = -10.0, 126.0, 120.0
DOOR_RISE = 8.0
HINGE_AXIS = Axis((HINGE_U,0,HINGE_Z),(0,1,0))
LATCH_U = 147.0
LATCH_LIFT = 3.3
SLEEVE_OD = 7.0
ROTATING_BORE = p.cadfits.slot_for(SLEEVE_OD, 0.25)
# Stop contact is 8 axial x 6 radial at the straight 186-degree end plane.
STOP_CONTACT_AREA = 48.0


def _ycyl(y0, length, radius, u=HINGE_U, z=HINGE_Z):
    return Pos(u,y0,z)*Cylinder(radius,length,rotation=(-90,0,0),
        align=(Align.CENTER,Align.CENTER,Align.MIN))


def _sector(y0,y1,r0,r1,a0,a1):
    angles=[a0+(a1-a0)*i/8 for i in range(9)]
    pts=[(HINGE_U+r*math.cos(math.radians(a)),HINGE_Z+r*math.sin(math.radians(a)))
        for r,aa in ((r1,angles),(r0,angles[::-1])) for a in aa]
    return Pos(0,y0,0)*extrude(Plane.XZ*Polygon(*pts,align=None),
        amount=y1-y0,dir=(0,1,0))


def _notches(shape, structural=False, rim_top=None):
    if structural:
        z=shape.bounding_box()
        top=z.max.Z if rim_top is None else rim_top
        for c in LATCH_V:
            shape+=box(122,130,c-17.5,c+17.5,z.min.Z,top)
            for a,b in ((c-17.5,c-9.5),(c+9.5,c+17.5)):
                shape+=box(122,159.9,a,b,z.min.Z,top)
    for c in LATCH_V:
        shape-=box(130,160.2,c-9.5,c+9.5,110,145)
    return shape


def _one(shape):
    assert len(shape.solids()) == 1, f'access door split into {len(shape.solids())} solids'
    return shape


def _hex(u,v,z0,z1,af):
    r=af/math.sqrt(3)
    pts=[(u+r*math.cos(math.radians(60*i)),v+r*math.sin(math.radians(60*i))) for i in range(6)]
    return Pos(0,0,z0)*extrude(Polygon(*pts,align=None),amount=z1-z0)


def receiver():
    """Stationary receiver with captive latch pillars, hinge forks and stops."""
    s=canopy_frame.outline(104,111.5)
    # Remove former mid-side PET clamp lobes; keep an 8 mm receiver rim.
    s-=box(8,16,61,83,103,112)
    s-=box(144,152,61,83,103,112)
    for u,v in canopy_frame.bolt_points():
        s-=z_cylinder(u,v,103,10,p.M4_BORE/2)
        s-=top_countersink(u,v,111.5,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
        # Seat on lobe shoulders, leaving socket access open.
        pad=box(u-7,u+7,v-7,v+7,111.5,112)
        pad-=z_cylinder(u,v,111,2,p.CSK_RECESS_D/2+0.5)
        s+=pad
    for c in HINGE_V:
        for a,b in ((c-10.3,c-5.3),(c+5.3,c+10.3)):
            cheek=_ycyl(a,b-a,9)+box(-28,-1,a,b,104,126)+box(-19,13,a,b,104,111.5)
            cheek+=_sector(a,b,0.1,18,186,200)
            s+=cheek
        s+=_sector(c-10.3,c+10.3,10,18,186,200)
        # External cage retains the nut at Y=c+10.3; no axial-stack change.
        cage=box(-16,-4,c+10.3,c+14.5,104,132)
        pocket=Pos(-10,c+10.3,126)*Rot(-90,0,0)*_hex(0,0,0,2.4,p.NUT_POCKET_AF)
        cage-=pocket
        cage-=box(-10-p.NUT_POCKET_AF/2,-10+p.NUT_POCKET_AF/2,c+10.3,c+12.7,126,133)
        s+=cage
        s-=_ycyl(c-11,27,2.25)
    for c in LATCH_V:
        s+=box(128,159.9,c-12,c+12,104,111.5)
        s+=box(138,156,c-9,c+9,111.5,125)
        # Index dog pockets, two discrete orientations, wider pillar shoulders.
        s+=box(143,151,c-9,c+9,114,125)
        s+=box(138,156,c-4,c+4,114,125)
        for du,dv in ((0,6),(6,0)):
            s-=box(147+du-1.75,147+du+1.75,c+dv-1.75,c+dv+1.75,121.7,125.1)
        s-=z_cylinder(147,c,109,18,2.25)
        s-=_hex(147,c,111.8,114,p.NUT_POCKET_AF)
        s-=box(146.5,161,c-p.NUT_POCKET_AF/2,c+p.NUT_POCKET_AF/2,111.8,114)
    # Moving PET-clamp tips/nuts recess into this receiver when closed.
    # Recesses retain a 3.2 mm floor and extend inward for initial opening sweep.
    for u,v in canopy_frame.clamp_points():
        cut=z_cylinder(u,v,107.2,5,5)+z_cylinder(u+4,v,107.2,5,5)
        cut+=box(u,u+4,v-5,v+5,107.2,112.2)
        if u == p.CANOPY_CELL_W/2:
            # R7 found sub-nozzle crescent walls where the shifted round
            # recess met the original 7.5 mm clamp lobe. Open the recess
            # to the inner edge; retain the 3.2 mm floor and 3 mm outer rim.
            # This removes material only, without moving any clamp seat.
            cut+=box(u-8,u+14,v-5,v+9,107.2,112.2) if v < 72 else box(u-8,u+14,v-9,v+5,107.2,112.2)
        else:
            # Open the side recess cleanly through its upper rim instead of
            # leaving a curved sub-nozzle crescent at the right outer edge.
            # The same 3.2 mm continuous lower receiver floor is retained.
            cut+=box(u-5,u+9,v-8,v+8,107.2,112.2)
        s-=cut
    return _one(s)


def moving_frame():
    s=Pos(0,0,DOOR_RISE)*canopy_frame.build()
    for u,v in canopy_frame.bolt_points():
        s+=z_cylinder(u,v,112,7.5,p.CSK_RECESS_D/2+0.1)
    s=_notches(s,structural=True,rim_top=119.5)
    # Local caps bridge notch corners through the remaining continuous side rim.
    for c in HINGE_V:
        eye=_ycyl(c-5,10,9)
        pts=[(-10,117),(8,112),(8,119.5),(-10,135)]
        web=Pos(0,c-5,0)*extrude(Plane.XZ*Polygon(*pts,align=None),amount=10,dir=(0,1,0))
        s+=eye+web+box(-19,8,c-5,c+5,112,126)
        s+=_sector(c-4,c+4,8.5,16,54,66)
        s-=_ycyl(c-6,12,ROTATING_BORE/2)
        # Raised eye supports stay outside the PET/cap seating stack.
        s-=box(0,14,c-5,c+5,119.5,150)
    return _one(s)


def cap():
    s=Pos(0,0,DOOR_RISE)*canopy_cap.build()
    for u,v in canopy_frame.bolt_points():
        s+=z_cylinder(u,v,120.5,3,p.CANOPY_CORNER_ACCESS_D/2+0.1)
    return _one(_notches(s,structural=True))


def sheet():
    return _one(_notches(Pos(0,0,DOOR_RISE)*canopy_sheet.roof()))


def hinge_sleeve():
    """Local origin on pivot at (0,0,0), axial Y, ends Y±5.3."""
    return _ycyl(-5.3,10.6,SLEEVE_OD/2,0,0)-_ycyl(-6,12,2.25,0,0)


def latch_sleeve():
    """Local pivot X=Y=0; actual installed deck Z retained."""
    s=z_cylinder(0,0,125,9,SLEEVE_OD/2)+z_cylinder(0,0,134,2,5.5)
    return s-z_cylinder(0,0,124,13,2.25)


def latch_lever():
    """Local pivot X=Y=0, locked along Y; actual deck Z retained.

    OPEN transform: Pos(0,0,3.3), then Rot(0,0,-90), then lower.
    """
    s=box(-6,6,-16,16,125.5,130.5)
    s+=box(-5,5,-15,-10,123.8,125.5)+box(-5,5,10,15,123.8,125.5)
    s+=box(-1.5,1.5,4.5,7.5,122.5,125.5)
    s-=z_cylinder(0,0,121,15,ROTATING_BORE/2)
    return _one(s)


def door_pose(shape,angle=0):
    return shape.rotate(HINGE_AXIS,-angle)


def print_pose(shape,kind):
    """Suggested poses; canonical print checks own final acceptance."""
    if kind == 'hinge_sleeve':
        s=Rot(90,0,0)*shape
    elif kind=='lever':
        s=Rot(180,0,0)*shape
    else:
        s=shape
    b=s.bounding_box()
    return Pos(-b.min.X,-b.min.Y,-b.min.Z)*s
