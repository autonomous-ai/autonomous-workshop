"""Roof-down band shields and floor extensions for the bolted guard bases.

The twelve-mm covered overlap uses a stepped interior: its entrance follows
R24.25 thumb-center envelopes; moving mushroom caps retain an upper pocket.
The existing guards remain separately bolted pieces within this enclosure.
"""
from functools import lru_cache
from math import radians,cos,sin
from build123d import Align,Axis,Circle,Cone,Plane,Polygon,Pos,Rot,extrude
from shapely.geometry import Point,Polygon as SPolygon,box
from shapely.ops import unary_union
from shapely.affinity import rotate,translate,scale
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink


def _disc(point,r):
    return Point(*point).buffer(r,resolution=p.APRON_CURVE_SEGMENTS)


def _capsule(a,b,r):
    from shapely.geometry import LineString
    return LineString([a,b]).buffer(r,resolution=p.APRON_CURVE_SEGMENTS)


def _extrude(poly,z0,z1):
    # Remove sub-nozzle Boolean fragments while keeping profile error below
    # .02mm, within the separate .25mm thumb and .5mm moving-part margins.
    poly=poly.simplify(p.APRON_PROFILE_TOL,preserve_topology=True)
    polys=list(poly.geoms) if hasattr(poly,'geoms') else [poly]
    pieces=[]
    for poly in polys:
        if poly.area<1e-8: continue
        face=Polygon(*list(poly.exterior.coords)[:-1],align=None)
        for hole in poly.interiors: face-=Polygon(*list(hole.coords)[:-1],align=None)
        pieces.append(Pos(0,0,z0)*extrude(face,amount=z1-z0,dir=(0,0,1)))
    if not pieces: return None
    shape=pieces[0]
    for piece in pieces[1:]: shape+=piece
    return shape


def thumb_centers(side):
    px,py=p.FLIPPER_PIVOTS[side]; dx,dy=p.FLIPPER_THUMB
    if side=='right': dx=-dx
    out=[]
    for i in range(p.APRON_SWEEP_SAMPLES):
        a=radians(p.FLIPPER_TRAVEL*i/(p.APRON_SWEEP_SAMPLES-1)*(1 if side=='left' else -1))
        out.append((px+dx*cos(a)-dy*sin(a),py+dx*sin(a)+dy*cos(a)))
    return out


def thumb_mask(side,extra=0):
    r=p.FLIPPER_THUMB_R+p.APRON_THUMB_CLEARANCE+p.APRON_THUMB_MARGIN+extra
    return unary_union([_disc(center,r) for center in thumb_centers(side)])


@lru_cache(maxsize=2)
def sweep_profiles(side):
    root,tip,length=p.FLIPPER_ROOT_R,p.FLIPPER_TIP_R,p.FLIPPER_BLADE_L
    blade=SPolygon(((0,root),(length,tip),(length,-tip),(0,-root)))
    blade=unary_union([blade,_disc((0,0),root),_disc((length,0),tip)])
    blade=rotate(blade,p.FLIPPER_BLADE_REST,origin=(0,0))
    rotor=unary_union([blade,_capsule((0,0),p.FLIPPER_TAIL_JOINT,p.FLIPPER_TAIL_R),
                      _capsule(p.FLIPPER_TAIL_JOINT,p.FLIPPER_THUMB,p.FLIPPER_TAIL_R)])
    cap=_disc(p.FLIPPER_TAIL_JOINT,p.FLIPPER_POST_CAP_R+p.APRON_SLOT_CLEARANCE)
    if side=='right': rotor=scale(rotor,xfact=-1,yfact=1,origin=(0,0)); cap=scale(cap,xfact=-1,yfact=1,origin=(0,0))
    body=[]; caps=[]; px,py=p.FLIPPER_PIVOTS[side]
    for i in range(p.APRON_SWEEP_SAMPLES):
        a=p.FLIPPER_TRAVEL*i/(p.APRON_SWEEP_SAMPLES-1)*(1 if side=='left' else -1)
        body.append(translate(rotate(rotor,a,origin=(0,0)),px,py))
        caps.append(translate(rotate(cap,a,origin=(0,0)),px,py))
    return unary_union(body).buffer(p.APRON_SLOT_CLEARANCE,resolution=p.APRON_CURVE_SEGMENTS),unary_union(caps)


@lru_cache(maxsize=2)
def band_profile(side):
    anchor=p.FLIPPER_FIXED_ANCHORS[side][0]
    r=p.FLIPPER_BAND_RADII[side]+p.BAND_T/2+p.FLIPPER_BAND_RADIAL_WOBBLE[side]+p.APRON_SLOT_CLEARANCE
    x,y=p.FLIPPER_TAIL_JOINT; profiles=[]
    for i in range(p.APRON_SWEEP_SAMPLES):
        a=radians(p.FLIPPER_TRAVEL*i/(p.APRON_SWEEP_SAMPLES-1))
        profile=_capsule(anchor,(x*cos(a)-y*sin(a),x*sin(a)+y*cos(a)),r)
        if side=='right':profile=scale(profile,xfact=-1,yfact=1,origin=(0,0))
        profiles.append(translate(profile,*p.FLIPPER_PIVOTS[side]))
    return unary_union(profiles)


def _guard_profiles(side,floor=False):
    px,py=p.FLIPPER_PIVOTS[side]; right=side=='right'; clear=p.APRON_GUARD_CLEARANCE
    base=p.FLIPPER_RIGHT_GUARD_OUTLINE if right else p.FLIPPER_GUARD_OUTLINE
    roof=p.FLIPPER_RIGHT_ROOF_OUTLINE if right else p.FLIPPER_GUARD_ROOF_OUTLINE
    mounts=p.FLIPPER_RIGHT_GUARD_MOUNTS if right else p.FLIPPER_GUARD_MOUNTS
    wx=p.FLIPPER_RIGHT_WALL_X if right else p.FLIPPER_GUARD_WALL_X
    wy=p.FLIPPER_RIGHT_WALL_Y if right else p.FLIPPER_GUARD_WALL_Y
    def world(poly):
        if right: poly=scale(poly,xfact=-1,yfact=1,origin=(0,0))
        return translate(poly,px,py).buffer(clear,resolution=p.APRON_CURVE_SEGMENTS)
    from parts.flipper_guard_base import stop_centers
    base_poly=SPolygon(base).buffer(-2*clear) if floor else SPolygon(base)
    stops=unary_union([_disc(point,p.FLIPPER_STOP_R) for point in stop_centers()])
    anchors=unary_union([_disc(point,p.FLIPPER_POST_CAP_R) for point in p.FLIPPER_FIXED_ANCHORS[side]])
    result=[(world(base_poly),(p.APRON_FLOOR_T if floor else p.FLIPPER_GUARD_BASE_T)+clear),
            (world(stops),p.FLIPPER_STOP_H+clear),
            (world(anchors),p.FLIPPER_POST_NECK_Z+p.FLIPPER_POST_NECK_H+p.FLIPPER_POST_CAP_H+clear),
            (_disc((px,py),p.FLIPPER_PEDESTAL_R+clear),p.FLIPPER_PEDESTAL_H+clear),
            (world(unary_union([_disc(point,p.FLIPPER_GUARD_MOUNT_R) for point in mounts]+[box(wx[0],wy[0],wx[1],wy[1])])),p.FLIPPER_GUARD_ROOF_Z+p.FLIPPER_GUARD_ROOF_T+clear)]
    if not floor: result.append((world(SPolygon(roof)),p.FLIPPER_GUARD_ROOF_Z+p.FLIPPER_GUARD_ROOF_T+clear))
    return result


def _layered_roof(outer,rows,top):
    """Monotone roof-down sections with a minimum printable planar web.

    A round opening of radius .8mm removes needle walls at intersecting
    clearance profiles. It only removes material; moving-part clearance can
    never decrease. Nested sections retain support from the layer above.
    """
    levels=sorted({p.APRON_FLOOR_T,top}|{h for _,h in rows if p.APRON_FLOOR_T<h<top})
    shape=None;r=p.APRON_MIN_WEB/2
    for lo,hi in zip(levels,levels[1:]):
        profile=outer.difference(unary_union([poly for poly,h in rows if h>(lo+hi)/2]))
        profile=profile.buffer(-r,resolution=p.APRON_CURVE_SEGMENTS).buffer(r,resolution=p.APRON_CURVE_SEGMENTS).intersection(profile)
        layer=_extrude(profile,lo,hi)
        if layer is not None:shape=layer if shape is None else shape+layer
    return shape


def floor_profile(side):
    """One flat3mm tray joins the existing guard outline to the apron floor.

    Keep the original guard footprint intact. The added footprint has no
    raised .3mm overlap strip, and the resulting mouth is10.1mm high.
    """
    x0,x1=p.APRON_X_BOUNDS[side];y0,y1=p.APRON_Y_BOUNDS;px,py=p.FLIPPER_PIVOTS[side]
    base=p.FLIPPER_RIGHT_GUARD_OUTLINE if side=='right' else p.FLIPPER_GUARD_OUTLINE
    mounts=p.FLIPPER_RIGHT_GUARD_MOUNTS if side=='right' else p.FLIPPER_GUARD_MOUNTS
    base=unary_union([SPolygon(base)]+[_disc(point,p.FLIPPER_GUARD_MOUNT_R) for point in mounts])
    if side=='right':base=scale(base,xfact=-1,yfact=1,origin=(0,0))
    base=translate(base,px,py)
    profile=box(x0,y0,x1,y1).difference(thumb_mask(side)).union(base)
    profile=profile.difference(box(p.CUP_DRAIN_X[0],p.CUP_DRAIN_Y[0],p.CUP_DRAIN_X[1],p.CUP_DRAIN_Y[1]))
    if side=='right':profile=profile.difference(box(p.LAUNCH_POCKET_X[0]-clearance(),p.LAUNCH_BASE_Y[0],x1,y1))
    for point in p.APRON_MOUNTS[side]:profile=profile.difference(_disc(point,p.APRON_ROOT_R+clearance()))
    r=p.APRON_MIN_WEB/2
    profile=profile.buffer(-r,resolution=p.APRON_CURVE_SEGMENTS).buffer(r,resolution=p.APRON_CURVE_SEGMENTS).intersection(profile).union(base)
    return profile


@lru_cache(maxsize=2)
def build(side='left',floor=False):
    x0,x1=p.APRON_X_BOUNDS[side]; y0,y1=p.APRON_Y_BOUNDS; t=p.APRON_WALL_T
    outer=box(x0,y0,x1,y1).difference(thumb_mask(side))
    top=p.APRON_ROOF_Z+p.APRON_ROOF_T
    slot_top=p.FLIPPER_ROTOR_Z+p.FLIPPER_ROTOR_T+p.APRON_SLOT_CLEARANCE
    rotor,cap=sweep_profiles(side)
    rows=_guard_profiles(side,floor)
    if not floor:
        cap_top=p.FLIPPER_POST_NECK_Z+p.FLIPPER_POST_NECK_H+p.FLIPPER_POST_CAP_H+p.APRON_SLOT_CLEARANCE
        rows += [(rotor,slot_top),(cap,cap_top),(band_profile(side),cap_top)]
    # Front end-panel drops into a blind slot; the central mullion has a
    # clearance well, and remains hung from its bolted roof bracket.
    sy=p.CANOPY_POST_Y[0]+p.CANOPY_END_PANEL_Y[0]
    half=p.CANOPY_PET_SLOT_W/2
    rows.append((box(p.CANOPY_CELL_W-p.CANOPY_END_JOIN_HALF_W-clearance(),
                     sy-p.CANOPY_END_JOIN_HALF_L-clearance(),
                     p.CANOPY_CELL_W+p.CANOPY_END_JOIN_HALF_W+clearance(),
                     sy+p.CANOPY_END_JOIN_HALF_L+clearance()),top))
    # Leave the full launcher enclosure and straight pull path unobstructed.
    if side=='right':
        rows.append((box(p.LAUNCH_POCKET_X[0]-clearance(),p.LAUNCH_BASE_Y[0],x1,y1),p.LAUNCH_GUARD_BOTTOM+p.LAUNCH_GUARD_T+clearance()))
    rows.append((box(p.CUP_DRAIN_X[0],p.CUP_DRAIN_Y[0],p.CUP_DRAIN_X[1],p.CUP_DRAIN_Y[1]),p.APRON_ROOF_Z))
    if floor:
        shape=_extrude(outer,0,p.APRON_FLOOR_T)
        for profile,height in rows:shape-=_extrude(profile,0,height)
    else:shape=_layered_roof(outer,rows,top)
    for x,y in p.APRON_MOUNTS[side]:
        if floor:
            shape-=z_cylinder(x,y,0,p.APRON_FLOOR_T,p.APRON_ROOT_R+clearance())
            continue
        shape+=z_cylinder(x,y,0,top,p.APRON_ROOT_R)
        shape-=z_cylinder(x,y,0,top,p.M4_BORE/2)
        shape-=z_cylinder(x,y,p.APRON_ROOT_LAND_Z,top-p.APRON_ROOT_LAND_Z,p.PLAYFIELD_ACCESS_D/2)
        shape-=top_countersink(x,y,p.APRON_ROOT_LAND_Z,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    # Through-deck drain opens into the shielded void, not onto a solid apron.
    shape-=bounded_box(*p.CUP_DRAIN_X,*p.CUP_DRAIN_Y,0,p.APRON_ROOF_Z)
    shape-=bounded_box(x0,x1,sy-half,sy+half,p.APRON_PET_GROOVE_FLOOR,top)
    if not floor: assert len(shape.solids())==1, f'{side} apron disconnected'
    return shape


def clearance(): return p.APRON_GUARD_CLEARANCE


def print_shape(side='left'):
    return Pos(0,0,p.APRON_ROOF_Z+p.APRON_ROOF_T)*Rot(180,0,0)*build(side)
