"""Mintfin's ellipse-lofted head and four-finger rear socket.

World geometry owns the Wish datums. Print transforms put each Y=20 split
face on Z=0. Rear socket is open in +Y and printed mouth up.
"""
from math import sqrt
from build123d import *
from params.face import *
from parts.face import outline_face, face_to_world, painted
from parts.decor import gill_world, horn_world
from features.joints import socket as family_socket


def _loft(stations):
    sections=[]
    for y,rx,rz in stations:
        plane=Plane(origin=(0,y,HEAD_CENTER_Z),x_dir=(1,0,0),z_dir=(0,1,0))
        sections.append(plane*Ellipse(rx,rz))
    return loft(sections)


def _world_box(y0,y1):
    return Pos(0,(y0+y1)/2,36)*Box(160,y1-y0,140)


def _head_outer():
    return _loft(HEAD_STATIONS)


def socket_world():
    """Use the common +Y seam-aligned spherical cavity and add preload lands."""
    r=JOINT['cavity_diameter']/2
    center=JOINT['ball_center']; bottom=center[1]-r-2
    s=family_socket(JOINT,bottom)
    # Four radial lands sit at the centers of the four unslit finger arcs.
    # Nominal cavity radius is r; 0.20 projection leaves 0.075 ball interference.
    for angle in (45,135,225,315):
        local=Pos(r+.10,0,0)*Box(.60,1.60,1.60)
        pad=local.rotate(Axis.Y,angle).translate(center)
        s=s+pad
    return s


def _decor_masks():
    return [gill_world(1),gill_world(-1),horn_world('pair',1),
            horn_world('pair',-1),horn_world('middle')]


def _mask_decor(shape):
    # Exact material masks: decoration and mint head occupy disjoint volumes.
    for mask in _decor_masks():
        shape=shape-mask
    return shape


def head_front_world():
    s=_head_outer() & _world_box(-30,20)
    # Stop residual loft tissue at the same indexing-lip plane; otherwise the
    # forehead/cheek intersection feathers to a thin wall above the lip.
    s=s-face_to_world(Pos(0,0,1.4)*Box(200,200,100,
        align=(Align.CENTER,Align.CENTER,Align.MIN)))
    # Cheek-shaped lip preserves full indexing around the non-elliptical face.
    # Constant offset keeps the concave cheek waist as thick as its lobes.
    # A long inward taper supports the cheek perimeter in the Y-split print pose.
    # Convert offset curves to explicit spline curves before STEP serialization.
    # Native offset-curve surfaces were omitted by the STEP transfer.
    rim_wire=offset(outline_face(),amount=1.6,kind=Kind.ARC).wires()[0]
    rim=Face(rim_wire.to_splines(degree=3,tolerance=0.0001))
    lip_blank=Pos(0,0,-3)*extrude(rim,amount=4.4,dir=(0,0,1))
    skirt=loft([Pos(0,0,-15)*rim.scale(.8),Pos(0,0,-3)*rim],ruled=True)
    s=s+face_to_world(lip_blank.fuse(skirt))
    # Face recess cuts all material forward of the common head floor n=0.
    cavity=Pos(0,0,0)*extrude(outline_face(1.0+.25/30),amount=35,dir=(0,0,1))
    s=s-face_to_world(cavity)
    # Magnet seats cut directly into solid floor; axes are face normal.
    for u,v in MAGNETS:
        cutter=Pos(u,v,-1.2)*Cylinder(MAGNET_D/2,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN))
        s=s-face_to_world(cutter)
    s=_mask_decor(s)
    return painted(s,'mint_head_front_with_indexed_face_pocket','mint')


def _gill_seat_roof_reliefs():
    """Open lateral mask roofs with print-supported 0.75:1 side ramps.

    Print height is worldY-20. Root contact at worldX=+/-29 remains
    over almost the full gill thickness; only the final0.1mm is eased.
    """
    y0, y1 = 29.9, HEAD_REAR_Y + 1.0
    profile = Polygon(
        (29.0 + .75*(y0-30.0), y0), (80.0, y0),
        (80.0, y1), (29.0 + .75*(y1-30.0), y1), align=None)
    right = Pos(0,0,-50) * extrude(profile, amount=200)
    return [right, right.mirror(Plane.YZ)]


def head_rear_world():
    # Shorten posterior loft stock5.6mm from nominal to preserve the first
    # barrel crown through25deg upward bend; measured width/height stay intact.
    # The socket is restored below, keeping its full retaining mouth.
    s=_head_outer() & _world_box(20,HEAD_REAR_Y)
    # Clear the closed body around the articulated socket, then fuse its floor.
    r=(JOINT['ball_diameter']+.25)/2
    clearance=Pos(*JOINT['ball_center'])*Rot(0,0,90)*Sphere(r)
    s=s-clearance
    free_finger_space=Pos(0,40.875,30)*Cylinder(r+2.3,20,rotation=(-90,0,0),align=(Align.CENTER,Align.CENTER,Align.MIN))
    s=s-free_finger_space
    socket=socket_world()
    # Web ties the socket floor into the shell inside, without filling its mouth.
    web=Pos(0,41,30)*Box(18,5,16)
    s=s+web
    # Clear host tissue first, then retain the socket's deliberate pad interference.
    s=s-clearance
    lip=JOINT['lip_axial_position_from_center']; mouth=JOINT['mouth_diameter']/2
    mouthcut=Pos(0,48,30)*Cylinder(mouth,12,rotation=(90,0,0),align=(Align.CENTER,Align.CENTER,Align.MAX))
    s=s-mouthcut
    s=s+socket
    s=_mask_decor(s)
    s=s.cut(*_gill_seat_roof_reliefs())
    return painted(s,'mint_head_rear_with_J00_four_finger_socket','mint')


def head_front():
    s=head_front_world().rotate(Axis.X,-90).translate((0,-36,20))
    return painted(s,'head_front_print_split_face_down','mint')


def head_rear():
    s=head_rear_world().rotate(Axis.X,90).translate((0,36,-20))
    # The entire flat construction seam is the bed datum; no raised tongues.
    return painted(s,'head_rear_print_split_face_down','mint')
