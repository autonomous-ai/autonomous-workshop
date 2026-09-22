"""Fixed Mintfin accessories; print shapes begin at bed Z=0.

World builders preserve the measured X/Y/Z datums. Each separate material
remains one named solid. Mating seats are exported as source tools for root
integration, with 0.20 mm adhesive allowance. No fit or print result claimed.
"""
from math import hypot
from build123d import Plane, Pos, Rot, Polygon, Ellipse, Rectangle, Circle, extrude, loft, Box, Align, Sphere, Cylinder, Cone
from cadgen import srgb
from params import DESIGN
from params.decor import *
from params.body import JOINTS
from features.joints import ball, y_cylinder


def finish(shape, name, color):
    shape.label = name
    shape.color = srgb(COLORS[color])
    return shape


def prism(points, thickness):
    return extrude(Polygon(*points, align=None), amount=thickness, dir=(0,0,1))


def elliptic_loft(stations):
    return loft([Pos(x,y,z)*Ellipse(rx,ry) for z,x,y,rx,ry in stations], ruled=True)


def feather_outline(base, tip, width):
    """Stout leaf with symmetric edge notches and a 1.2 mm blunt tip."""
    dx,dy=tip[0]-base[0],tip[1]-base[1]
    length=hypot(dx,dy); ux,uy=dx/length,dy/length; vx,vy=-uy,ux
    # Notch valleys remain outside the stout shaft, with >=1mm slot mouths.
    stations=[(0,0.32),(.16,.72),(.24,1),(.29,.65),(.34,.98),(.43,.88),(.48,.5),(.53,.82),(.62,.68),(.67,.32),(.72,.55),(.86,.3),(1,HORN_TIP/width)]
    def p(t,w,s): return (base[0]+t*dx+s*w*width/2*vx,base[1]+t*dy+s*w*width/2*vy)
    points=[p(t,w,1) for t,w in stations]+[p(t,w,-1) for t,w in reversed(stations)]
    return [(min(37.5,x),min(35,z)) for x,z in points]


def gill_print(side=1):
    body=prism(GILL_ROOT_PROFILE,GILL_THICKNESS)
    leaves=[]; shafts=[]
    for base,tip,width in GILL_LEAVES:
        leaves.append(prism(feather_outline(base,tip,width),GILL_THICKNESS))
        dx,dy=tip[0]-base[0],tip[1]-base[1]
        # Raised convex-looking ruled keel, ending short of the blunt leaf tip.
        a=(base[0],base[1]); b=(base[0]+.88*dx,base[1]+.88*dy)
        length=hypot(dx,dy); vx,vy=-dy/length,dx/length
        foot=[(a[0]+vx*1.3,a[1]+vy*1.3),(b[0]+vx*.65,b[1]+vy*.65),(b[0]-vx*.65,b[1]-vy*.65),(a[0]-vx*1.3,a[1]-vy*1.3)]
        top=[(a[0]+vx*.5,a[1]+vy*.5),(b[0]+vx*.45,b[1]+vy*.45),(b[0]-vx*.45,b[1]-vy*.45),(a[0]-vx*.5,a[1]-vy*.5)]
        shafts.append(loft([Pos(0,0,GILL_THICKNESS)*Polygon(*foot,align=None),Pos(0,0,GILL_THICKNESS+GILL_SHAFT_HEIGHT)*Polygon(*top,align=None)],ruled=True))
    body=body.fuse(*leaves,*shafts)
    if side<0: body=body.mirror(Plane.YZ)
    return finish(body,'gills_right' if side>0 else 'gills_left','coral')


def gill_world(side=1):
    # local XY is world XZ; plate normal faces toward the animal's nose.
    shape=Pos(*GILL_ROOT)*Rot(90,0,0)*gill_print(1)
    if side<0: shape=shape.mirror(Plane.YZ)
    return finish(shape,'gills_right' if side>0 else 'gills_left','coral')


def gill_seat(side=1):
    shape=Pos(GILL_ROOT[0]-.2,GILL_ROOT[1]-GILL_THICKNESS-.2,GILL_ROOT[2]-11.2)*Box(7.4,GILL_THICKNESS+.4,24.4,align=(Align.MIN,Align.MIN,Align.MIN))
    return shape if side>0 else shape.mirror(Plane.YZ)


def claw_print():
    profiles=[]
    for z,width,length,nose,bevel in CLAW_SECTIONS:
        outline=[(-width/2,0),(width/2,0),
                 (width/2,-length+bevel),(nose/2,-length),
                 (-nose/2,-length),(-width/2,-length+bevel)]
        profiles.append(Pos(0,0,z)*Polygon(*outline,align=None))
    return finish(loft(profiles,ruled=True),'claw','charcoal')


def leg_print(side=1):
    shape=elliptic_loft(LEG_STATIONS)
    # Flat keyed pad at the inner ankle; root integrates the complementary seat.
    pad=Pos(-11,6,15)*Box(*LEG_KEY,align=(Align.CENTER,Align.CENTER,Align.MIN))
    # The ankle key formerly began with an unsupported outward ledge.
    # Grow its support outward one millimetre per millimetre of height.
    buttress=loft([Pos(-7,6,11)*Rectangle(5,5),
                   Pos(-11,6,15)*Rectangle(5,5)],ruled=True)
    shape=shape.fuse(pad,buttress)
    # One full-height planar toe face has no slot roofs or thin toe skirts.
    # Three separate charcoal claws bond externally to this broad flat face.
    front=Pos(0,LEG_TOE_FACE_Y,0)*Box(100,100,100,
        align=(Align.CENTER,Align.MAX,Align.MIN))
    shape=shape.cut(front)
    if side<0: shape=shape.mirror(Plane.YZ)
    return finish(shape,'leg_right' if side>0 else 'leg_left','mint')


def leg_world(index):
    x,y,z=LEG_FEET[index]
    return Pos(x,y,z)*leg_print(1 if x>0 else -1)


def leg_seat(index):
    x,y,z=LEG_FEET[index]; side=1 if x>0 else -1
    return Pos(x-side*11,y+6,15)*Box(LEG_KEY[0]+.4,LEG_KEY[1]+.4,LEG_KEY[2]+.4,align=(Align.CENTER,Align.CENTER,Align.MIN))


def claw_world(index,claw_index):
    x,y,z=LEG_FEET[index]; side=1 if x>0 else -1
    cx,cy,cz=CLAW_CENTERS[claw_index]
    return Pos(x+side*cx,y+cy,z+cz)*claw_print()


def tapered_horn(size,lean):
    w,d,h=size
    # Bed sits on the key tip: 2mm keyed tongue, growing 45 degrees into base.
    keyw,keyd=min(w-4,4),min(d-4,4)
    flare=HORN_FLARE_RISE_RATIO*max((w-keyw)/2,(d-keyd)/2)
    shoulder_z=KEY_DEPTH+flare
    remaining=h-flare
    stations=[(0,0,0,keyw/2,keyd/2),(KEY_DEPTH,0,0,keyw/2,keyd/2),(shoulder_z,0,0,w/2,d/2),(shoulder_z+remaining*.30,lean[0]*.2,lean[1]*.2,w*.39,d*.39),(shoulder_z+remaining*.65,lean[0]*.7,lean[1]*.7,w*.22,d*.22),(KEY_DEPTH+h,lean[0],lean[1],HORN_TIP/2,HORN_TIP/2)]
    return elliptic_loft(stations)


def horn_print(kind='middle',side=1):
    p=HORN_MIDDLE if kind=='middle' else HORN_PAIR
    shape=tapered_horn(p['size'],p['lean'])
    if side<0: shape=shape.mirror(Plane.YZ)
    return finish(shape,'horn_'+kind,'charcoal')


def horn_world(kind='middle',side=1):
    p=HORN_MIDDLE if kind=='middle' else HORN_PAIR
    x,y,z=p['base']
    return Pos(side*x,y,z-KEY_DEPTH)*horn_print(kind,side)


def spike_print():
    # Broad flat adhesive base; the crown supplies the matching planar seat.
    # Head horns retain their separate keyed construction.
    w,d,h=SPIKE_SIZE
    stations=[]
    for height_ratio,width_ratio,lean_ratio in SPIKE_TAPER_STATIONS:
        rx=HORN_TIP/2 if width_ratio is None else w*width_ratio/2
        ry=HORN_TIP/2 if width_ratio is None else d*width_ratio/2
        stations.append((h*height_ratio,SPIKE_LEAN[0]*lean_ratio,
                         SPIKE_LEAN[1]*lean_ratio,rx,ry))
    return finish(elliptic_loft(stations),'dorsal_spike','charcoal')


def front_spike_print():
    return finish(elliptic_loft(FRONT_SPIKE_STATIONS),'dorsal_spike_front','charcoal')


def spike_position(index):
    if index == 0: return FRONT_SPIKE_BASE
    s=DESIGN['segments'][index]
    return (0,s['center'][1],s['center'][2]+s['height']/2-SPIKE_CROWN_SEAT_DEPTH)


def spike_world(index):
    return Pos(*spike_position(index))*(front_spike_print() if index==0 else spike_print())


def belly_print(index):
    s=DESIGN['segments'][index]
    scale=s['width']/DESIGN['segments'][0]['width']
    # Repair r0001: a constant section removes the measured thin bevel and
    # the last patch's reverse flare. Both broad faces remain parallel.
    width,height=((6.0,2.2) if index==6 else (4.8,2.2)) if index>=6 else (BELLY_FIRST_WIDTH*scale,BELLY_FIRST_HEIGHT*scale)
    # Assembly clearance: retain the oval read with 1.5mm relief per side.
    if index==0: width=BELLY_FIRST_PRINT_WIDTH
    profile=Ellipse(width/2,height/2)
    shape=extrude(profile,amount=BELLY_THICKNESS,dir=(0,0,1))
    return finish(shape,'belly_'+str(index+1),'cream')


def belly_position(index):
    s=DESIGN['segments'][index]; scale=s['width']/DESIGN['segments'][0]['width']
    if index>=6:
        return (0,115.4 if index==6 else BELLY_LAST_CENTER_Y,s['center'][2]-s['height']/2)
    front_y=s['center'][1]-1.2
    return (0,front_y,s['center'][2]-s['height']/2+BELLY_FIRST_HEIGHT*scale/2)


def belly_world(index):
    rotation=Rot(0,0,0) if index>=6 else Rot(90,0,0)
    return Pos(*belly_position(index))*rotation*belly_print(index)


def tail_full_world():
    """Five-lobed fan with J08 integral ball, cleared from the parent socket."""
    plane=Plane(origin=(0,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
    fan_half=plane.location*prism(TAIL_OUTLINE,TAIL_HALF_THICKNESS)
    fan=fan_half.fuse(fan_half.mirror(Plane.YZ))
    j=JOINTS[8]; _,joint_y,joint_z=j['ball_center']
    # Remove leading fan stock within the socket wall envelope plus clearance;
    # the ball is added AFTER this cut so its spherical mating surface remains.
    from parts.body import parent_clearance, _pitch_prism
    cutters=list(parent_clearance(8))
    # The fan reaches forward over the two final dorsal spikes and the
    # preceding ball. Clear their actual operating envelope as well.
    previous=JOINTS[7]; _,by,bz=previous['ball_center']
    br=previous['ball_diameter']/2+.3
    cutters.append(_pitch_prism([(y,z) for y in (by-br,by+br)
                                for z in (bz-br,bz+br)],br,j['ball_center']))
    for index in (6,7):
        _,sy,sz=spike_position(index); profile=[]
        for h,w,lean in SPIKE_TAPER_STATIONS:
            half=.6 if w is None else SPIKE_SIZE[1]*w/2
            profile.extend([(sy+SPIKE_LEAN[1]*lean-half-.3,sz+SPIKE_SIZE[2]*h+.3),
                            (sy+SPIKE_LEAN[1]*lean+half+.3,sz+SPIKE_SIZE[2]*h+.3)])
        cutters.append(_pitch_prism(profile,4.3,j['ball_center']))
    fan=fan.cut(*cutters)
    root_ball=ball(j,TAIL_NECK_REAR_Y-2)
    # Keep the full-width fan root and constant-section collar behind the parent
    # clearance envelope, instead of leaving a thin tongue beside the ball.
    flare_start=TAIL_NECK_FLARE_START_Y
    flare_end=TAIL_NECK_FLARE_REAR_Y
    flare=Pos(0,flare_start,joint_z)*Box(
        2*TAIL_NECK_FLARE_RADIUS,flare_end-flare_start,
        2*TAIL_NECK_FLARE_RADIUS,
        align=(Align.CENTER,Align.MIN,Align.CENTER))
    return fan.fuse(root_ball,flare)


def tail_world(side=1):
    whole=tail_full_world()
    halfspace=Pos(0,0,0)*Box(100,200,120,align=(Align.MIN,Align.MIN,Align.MIN))
    if side<0: halfspace=halfspace.mirror(Plane.YZ)
    intersection=whole.intersect(halfspace)
    shape=intersection[0] if isinstance(intersection,list) else intersection
    # Sagittal adhesive reservoirs remain accessible from the flat bed face.
    plane=Plane(origin=(0,0,0),x_dir=(0,1,0),z_dir=(side,0,0))
    # Build in +X and mirror to avoid a handed local-axis ambiguity.
    cutters=[]
    for y,z in TAIL_KEY_CENTERS:
        cutter=Plane(origin=(0,y,z),x_dir=(0,1,0),z_dir=(1,0,0)).location*extrude(Circle(TAIL_KEY_RADIUS),amount=TAIL_KEY_DEPTH,dir=(0,0,1))
        cutters.append(cutter if side>0 else cutter.mirror(Plane.YZ))
    shape=shape.cut(*cutters)
    return finish(shape,'tail_right' if side>0 else 'tail_left','coral')


def tail_print(side=1):
    # Each whole half has its largest sagittal cross-section on the bed. The
    # spherical ball shrinks away from that plane, without a suspended sphere.
    shape=tail_world(side)
    if side<0: shape=shape.mirror(Plane.YZ)
    plane=Plane(origin=(0,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
    shape=plane.location.inverse()*shape
    return finish(shape,'tail_right' if side>0 else 'tail_left','coral')
