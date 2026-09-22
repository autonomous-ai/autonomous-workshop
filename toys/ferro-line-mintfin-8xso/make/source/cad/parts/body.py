"""Elliptical barrels in assembly coordinates, split on the largest section.
The physics-untested lesson is addressed by a real-size coupon and explicit
physical uncertainty, never a simulated claim of friction or snap force.
"""
from functools import lru_cache
from math import sqrt, sin, cos, radians
from build123d import *
from params.body import SEGMENTS,JOINTS,SEAM,BODY08_SEAM
from features.joints import socket,ball,socket_cavity,y_cylinder,preload_pads
from parts.decor import belly_world,spike_world,leg_world

def barrel(i, clearance=0):
    p=SEGMENTS[i]; _,cy,cz=p['center']; length=p['shell_axial_length']
    sections=[]
    stations=[(-length/2-1.2,.76),(-length/3-1.2,.90),(-length/6-1.2,.975),(-1.2,1.0),(1.2,1.0),(length/6+1.2,.975),(length/3+1.2,.90),(length/2+1.2,.76)]
    for offset,scale in stations:
        y=cy+offset
        plane=Plane(origin=(0,y,cz),x_dir=(1,0,0),z_dir=(0,1,0))
        sections.append(plane*Ellipse(p['width']*scale/2+clearance,p['height']*scale/2+clearance))
    return loft(sections,ruled=True)

def _convex_hull(points):
    points=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def _pitch_prism(profile, half_width, center):
    # Conservative YZ envelope extruded over the entire parent's width. One
    # simple prism avoids coincident multi-cutter Boolean slivers and huge B-reps.
    _,cy,cz=center; points=[]
    for n in range(11):
        a=radians(-2.5*n)
        for y,z in profile:
            dy,dz=y-cy,z-cz
            points.append((cy+dy*cos(a)-dz*sin(a),cz+dy*sin(a)+dz*cos(a)))
    plane=Plane(origin=(-half_width,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
    return plane.location*extrude(Polygon(*_convex_hull(points),align=None),amount=2*half_width)


@lru_cache(maxsize=None)
def parent_clearance(i):
    """Conservative inverse-pitch clearance; actual motion must still be tested."""
    incoming=JOINTS[i]; _,iy,iz=incoming['ball_center']
    # A declared envelope may preserve an already reviewed child clearance
    # after a small parent lip extension; J01 retains only 0.1mm axial allowance.
    lip=iy+incoming.get('parent_clearance_lip_offset',
                        incoming['lip_axial_position_from_center']+.3)
    r=incoming['cavity_diameter']/2+2.3
    cup=y_cylinder(r,iy-8,lip,iz)
    axis=Axis(incoming['ball_center'],(1,0,0))
    if i:
        q=SEGMENTS[i-1]; _,qy,qz=q['center']; length=q['shell_axial_length']
        stations=[(-length/2-1.2,.76),(-length/3-1.2,.90),(-length/6-1.2,.975),(-1.2,1),(1.2,1),(length/6+1.2,.975),(length/3+1.2,.90),(length/2+1.2,.76)]
        top=qz+q['height']/2-1.2+.3
        profile=[(qy+d,min(top,qz+q['height']*scale/2+.3)) for d,scale in stations]
        profile += [(qy+d,qz-q['height']*scale/2-.3) for d,scale in stations]
        if i==8:
            profile=[(y,z) for y in (qy-.3,qy+3.8)
                     for z in (qz-q['height']/2-.3,top)]
        width=q['width']/2+.3
    else:
        from params.face import HEAD_STATIONS,HEAD_CENTER_Z,HEAD_REAR_Y,HEAD_REAR_HALF_HEIGHT
        stations=[s for s in HEAD_STATIONS if 20<=s[0]<HEAD_REAR_Y]+[(HEAD_REAR_Y,21.922608,HEAD_REAR_HALF_HEIGHT)]
        profile=[(y,HEAD_CENTER_Z+rz+.3) for y,rx,rz in stations]
        profile += [(y,HEAD_CENTER_Z-rz-.3) for y,rx,rz in stations]
        width=33.55
    return [*(cup.rotate(axis,-5*n) for n in range(6)),
            _pitch_prism(profile,width,incoming['ball_center'])]

@lru_cache(maxsize=None)
def body_stock(i):
    p=SEGMENTS[i];cy=p['center'][1]
    incoming=JOINTS[i];outgoing=JOINTS[i+1]
    # The socket cavity is cut in both construction halves to avoid a hidden plug.
    _,jy,jz=outgoing['ball_center']; r=outgoing['cavity_diameter']/2
    end=jy+outgoing['lip_axial_position_from_center']
    shell=barrel(i)
    if i==7:
        # Preserve the measured full section at Y123.1, while placing the
        # connecting land behind the preceding socket's swept lip envelope.
        plane=Plane(origin=(0,cy,p['center'][2]),x_dir=(1,0,0),z_dir=(0,1,0))
        shell=plane.location*extrude(Ellipse(p['width']/2,p['height']/2),amount=3.5)
    top=p['center'][2]+p['height']/2-1.2
    shell=shell.cut(Pos(0,cy,top+50)*Box(200,200,100))
    # Clear BOTH barrel and outgoing housing before restoring the full ball.
    # Otherwise the housing reinstates the measured parent-socket clash.
    stock=shell.fuse(y_cylinder(r+2,cy-1.6,end,jz))
    stock=stock.cut(*parent_clearance(i))
    if i>=6:
        bottom=p['center'][2]-p['height']/2+1.2
        stock=stock.cut(Pos(0,cy,bottom-50)*Box(200,200,100))
    return stock

@lru_cache(maxsize=None)
def complete_body(i):
    p=SEGMENTS[i];cy=p['center'][1]
    incoming=JOINTS[i];outgoing=JOINTS[i+1]
    _,jy,jz=outgoing['ball_center'];r=outgoing['cavity_diameter']/2
    end=jy+outgoing['lip_axial_position_from_center']
    shape=body_stock(i).fuse(ball(incoming,cy))
    shape=shape-(Pos(0,jy,jz)*Rot(0,0,90)*Sphere(r))
    shape=shape-y_cylinder(outgoing['mouth_diameter']/2,jy,end+2,jz)
    root_y=BODY08_SEAM if i==7 else cy
    start=max(root_y+1.6,jy+outgoing['lip_axial_position_from_center']-8)
    length=end-start+1
    shape=shape-[Pos(0,start+length/2,jz)*Box(1,length,2*r+6),
                 Pos(0,start+length/2,jz)*Box(2*r+6,length,1)]
    shape=shape.fuse(*preload_pads(outgoing))
    # External cream plates bond to the flat front end: no buried pocket roof.
    # A planar crown seat removes the former narrow key-pocket lips.
    # Full-depth open ankle corners avoid razor-thin organic pocket margins.
    # The feet remain at Wish datums, bonding against these open faces.
    for foot in range(4):
        lx,ly,_=__import__('params').DESIGN['legs']['feet'][foot]
        side=1 if lx>0 else -1
        shape=shape.cut(Pos(side*(18.5+50),ly+2,19-50)*Box(100,30,100))
    assert len(shape.solids())==1,('body',i,len(shape.solids()))
    return shape

def body_half(i,side,print_pose=True):
    p=SEGMENTS[i];cy=p['center'][1];cz=p['center'][2]
    sign=-1 if side=='front' else 1
    # Final barrel retains its measured widest section; only its bond seam moves.
    seam=BODY08_SEAM if i==7 else cy
    half=complete_body(i)&(Pos(0,seam+sign*100,50)*Box(240,200,240))
    if side=='front' and i in (0,1,2,3,4,5):
        # Measured repair: the inverse parent envelope feathered this land
        # below 1.2mm. Project its leading section through a flat axial land.
        incoming=JOINTS[i]; outgoing=JOINTS[i+1]
        _,iy,iz=incoming['ball_center']
        plate=body_stock(i)&(Pos(0,cy-.6,50)*Box(240,1.2,240))
        plane=Plane(origin=(0,cy-1.201,0),x_dir=(1,0,0),z_dir=(0,1,0))
        for cutter in parent_clearance(i):
            profile=section(cutter,section_by=plane)
            if profile.faces():
                plate=plate.cut(extrude(profile,amount=1.402,dir=(0,1,0)))
        sphere_and_stem=ball(incoming,cy)&(Pos(0,cy-100,50)*Box(240,200,240))
        # Restore a printable rear 45-degree tangent heel without changing
        # the sphere/contact front. Exact joint motion remains to be checked.
        tangent=incoming['ball_diameter']/2/sqrt(2)
        depth=cy-iy-tangent
        heel=Pos(0,iy+tangent,iz)*Rot(-90,0,0)*Cone(
            tangent,max(0,tangent-depth),depth,
            align=(Align.CENTER,Align.CENTER,Align.MIN))
        half=plate.fuse(sphere_and_stem,heel).cut(socket_cavity(outgoing))
        if i==5:
            # A straight opening prevents the outgoing cavity's small cap
            # from feathering into the constant-thickness front land.
            _,oy,oz=outgoing['ball_center']
            radius=sqrt((outgoing['cavity_diameter']/2)**2-(oy-cy)**2)
            half=half.cut(y_cylinder(radius,cy-1.3,cy+.1,oz))
        for lx,ly,_ in __import__('params').DESIGN['legs']['feet']:
            side_sign=1 if lx>0 else -1
            half=half.cut(Pos(side_sign*(18.5+50),ly+2,19-50)*Box(100,30,100))
    if side=='front' and i==6:
        # Small-barrel repair: a 1.2mm full-section front land replaces the
        # unsupported thin crescent around the eccentrically placed parent cup.
        incoming=JOINTS[i]; outgoing=JOINTS[i+1]
        _,iy,iz=incoming['ball_center']; _,oy,oz=outgoing['ball_center']
        # Straight through-opening preserves the full axial plate thickness.
        # The former oblique loft cut feathered the entire lower crescent.
        radius=sqrt((outgoing['cavity_diameter']/2)**2-(oy-cy)**2)
        relief=y_cylinder(radius,cy-1.3,cy+.1,oz)
        plate=body_stock(i) & (Pos(0,cy-.6,50)*Box(240,1.2,240))
        plate=plate.cut(relief)
        # Carry the leading clearance profile through this thin land instead
        # of retaining a taper that runs down to zero axial thickness.
        plane=Plane(origin=(0,cy-1.201,0),x_dir=(1,0,0),z_dir=(0,1,0))
        for cutter in parent_clearance(i):
            profile=section(cutter,section_by=plane)
            if profile.faces():
                plate=plate.cut(extrude(profile,amount=1.402,dir=(0,1,0)))
        sphere_and_stem=ball(incoming,cy)&(Pos(0,cy-100,50)*Box(240,200,240))
        half=plate.fuse(sphere_and_stem).cut(socket_cavity(outgoing))
    if side=='front' and i==7:
        # The front land spans the measured centre to the posterior seam.
        # Its rear bridge joins the ball root behind the swept parent lip.
        incoming=JOINTS[i]; outgoing=JOINTS[i+1]
        _,iy,iz=incoming['ball_center']; _,oy,oz=outgoing['ball_center']
        radius=sqrt((outgoing['cavity_diameter']/2)**2-(oy-seam)**2)
        relief=y_cylinder(radius,cy-.1,seam+.1,oz)
        plate=body_stock(i)&(Pos(0,(cy+seam)/2,50)*Box(240,seam-cy,240))
        plate=plate.cut(relief)
        sphere_and_stem=ball(incoming,seam)&(Pos(0,seam-100,50)*Box(240,200,240))
        # Printable heel joins the BACK 45-degree latitude of the unchanged
        # sphere. Its radius shrinks 1:1 toward the seam, never flares outward.
        # The existing D4.2 neck remains fused where it is wider than the heel.
        tangent=incoming['ball_diameter']/2/sqrt(2)
        heel_start=iy+tangent
        heel_depth=seam-heel_start
        heel=Pos(0,heel_start,iz)*Rot(-90,0,0)*Cone(
            tangent,tangent-heel_depth,heel_depth,
            align=(Align.CENTER,Align.CENTER,Align.MIN))
        half=plate.fuse(sphere_and_stem,heel).cut(socket_cavity(outgoing))
    if side=='rear':
        if i==1:
            # The inverse incoming-cup cut closed in <1mm and left an 11.1mm2
            # unsupported roof. A narrow YZ diamond closes over 1.72mm, with
            # <45-degree walls, without drilling through the dorsal crown.
            plane=Plane(origin=(-5.5,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
            # Lower ramp is Z37.70 + 0.9*(Y-cy): its plane stays
            # 2.009mm outside the outgoing spherical cavity. The first
            # 0.096mm retains the original parent-clearance boundary.
            profile=Polygon((cy-.01,37.691),(cy-.01,40.309),
                            (cy+1.4444444444,39.0),align=None)
            half=half.cut(plane.location*extrude(profile,amount=11,dir=(0,0,1)))
            # Open the small tip membrane into the existing central slit,
            # following the same protected lower ramp rather than cutting
            # a low rectangular notch into the outgoing socket wall.
            plane=Plane(origin=(-1.4,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
            profile=Polygon((cy+1.0,38.60),(cy+1.0,39.60),
                            (cy+1.75,39.60),(cy+1.75,39.275),align=None)
            half=half.cut(plane.location*extrude(profile,amount=2.8,dir=(0,0,1)))
        if i==0:
            # Head clearance leaves a measured 2.7mm2 steep crown ledge.
            # This local subtractive ramp restores a supported <=45deg rise
            # while preserving the full crown behind its first axial millimetre.
            plane=Plane(origin=(-100,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
            profile=Polygon((cy-.01,45.791),(cy+1.1,46.79),
                            (cy+1.1,100),(cy-.01,100),align=None)
            half=half.cut(plane.location*extrude(profile,amount=200))
        # Open the small tangent cavity remnant to the construction seam.
        # The front half supplies the continuous bottom after bonding.
        j=JOINTS[i+1]; _,jy,jz=j['ball_center']; r=j['cavity_diameter']/2
        # J01 anterior shift: a 2 mm opening removes the two measured
        # sub-2 mm incoming-clearance wedges without altering the mouth/pads.
        root_opening_depth=2.0 if i==0 else 1.2
        d=jy-(seam+root_opening_depth)
        if abs(d)<r and jy-r<seam+root_opening_depth:
            half=half.cut(y_cylinder(sqrt(r*r-d*d),seam-.1,seam+root_opening_depth,jz))
    if side=='rear' and i==6:
        # Open the incoming-cup cap into the existing horizontal finger slit.
        # The lower boundary rises 1:1 in YZ (45 degrees in print pose).
        # Side faces stay >2 mm from the actual outgoing spherical cavity;
        # subtractive clearance does not restore stock inside the parent sweep.
        plane=Plane(origin=(-6.4,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
        profile=Polygon((cy-.01,39.77),(cy-.01,42.3),
                        (cy+1.7,42.3),(cy+1.7,41.48),align=None)
        half=half.cut(plane.location*extrude(profile,amount=12.8,dir=(0,0,1)))
    # Shared seam is a broad planar bonding datum; no loose joint pins.
    if print_pose:
        half=Rot(sign*90,0,0)*Pos(0,-seam,-cz)*half
        bb=half.bounding_box();half=Pos(0,0,-bb.min.Z)*half
    assert len(half.solids())==1,('half',i,side,len(half.solids()))
    half.color=Color(169/255,205/255,190/255)
    half.label=f'body_{i+1:02d}_{side}_green'
    return half
