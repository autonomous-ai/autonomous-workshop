"""Civic Skyline: original stylized architecture; all dimensions mm [assumed].
Architectural and cultural provenance is recorded in city_spec.md / RESEARCH.md.
No licensed reference mesh or external component geometry is used.
"""
from build123d import *
from functools import lru_cache

# [assumed] printable tabletop proportions, not architectural scale models.
SQUARE = 42.0
FRAME = 24.0
PANEL = 192.0
BOARD = 384.0
BOARD_H = 5.0
SEAT_Z = 2.4
TILE_GAP = 0.5
POCKET_CORNER = 2.0
TILE_H = BOARD_H - SEAT_Z
RELIEF_H = 1.4
RELIEF_Z = BOARD_H - 0.2
PLINTH = [(0,1.0),(2,1.0),(4,0.93),(7,0.93),(9,0.78)]
BASE_RADIUS = dict(king=16,queen=16,bishop=15,knight=15,rook=15,pawn=13)
HEIGHTS = dict(king=86,queen=76,bishop=64,knight=58,rook=52,pawn=40)
IVORY = (0.91,0.85,0.69)
MIDNIGHT = (0.10,0.22,0.25)
TILE_COLOR = (0.17,0.30,0.31)
# Each tuple is width/depth/start/height. Every slab overlaps its predecessor.
KING_TIERS = [(25,22,8,10),(23,20,17,9),(20,17,25,10),(16,14,34,29),(12,11,62,6),(8,8,67,6),(5,5,72,7)]
QUEEN_TIERS = [(23,21,8,11),(18,17,18,30),(20,16,47,4)]
# A truncated 3.2 mm prow retains the unmistakable wedge without a knife edge.
BISHOP_POLY = [(-11,8),(11,8),(1.6,-13),(-1.6,-13)]
BISHOP_TIERS = [(1.0,8,7),(0.94,14,41),(1.04,54,3),(0.90,56,4)]
KNIGHT_POLY = [(-10,8),(9,8),(9,24),(13,30),(13,36),(7,40),(5,47),(1,46),(-3,49),(-6,42),(-10,33)]
KNIGHT_DEPTH = 11.0
ROOK_BODY = (21,19,8,38)
ROOK_CROWN = (24,22,44,5)
ROOK_BATTLEMENT = (6,6,47,5)
PAWN_STEM = (11,11,8,15)
PAWN_TANK_R = 8.5
PAWN_TANK_Z = 22.0
PAWN_TANK_H = 11.0
PAWN_ROOF_H = 7.0
PAWN_TIP_R = 1.8
GROOVE_DEPTH = 0.65
GROOVE_WIDTH = 1.3
WINDOW_PITCH = 4.0
# radius, arch centre Z, bottom Z, extrusion depth: actual stepped fan surfaces.
QUEEN_FANS = [(10,51,48,14),(7.6,57,54,11),(5.2,63,60,8),(3.2,69,65,5)]
KING_CROSS = (9,3.2,81,3.2)
KING_CROSS_STEM = (3.2,3.2,79,7)
BISHOP_CAP_R = 5.0
BISHOP_CAP_Z = 57.0
BISHOP_CAP_H = 7.0
# Relief icon positions in global XY: five connected cultural places around perimeter.
GLYPH_CENTERS = [('chinatown',75,12,0),('staten',285,12,0),('williamsburg',12,108,90),('bronx',110,372,180),('queens',372,276,90)]
GLYPH_HALF = 16.0
LINE_W = 1.5

assert SQUARE * 8 + FRAME * 2 == BOARD
assert TILE_H >= 2.4 and TILE_GAP >= 0.4
assert max(BASE_RADIUS.values()) * 2 < SQUARE

def slab(w,d,z,h,x=0,y=0):
    return Pos(x,y,z) * Box(w,d,h,align=(Align.CENTER,Align.CENTER,Align.MIN))

def rectangular_shoulder(w0,d0,z0,w1,d1,z1):
    # [assumed] Rising shoulders support projecting masonry with slope margin.
    return loft([Plane.XY.offset(z0)*Rectangle(w0,d0),
                 Plane.XY.offset(z1)*Rectangle(w1,d1)],ruled=True)

def profile(points,height,z=0):
    return Pos(0,0,z) * extrude(Polygon(*points,align=None),amount=height)

def plinth(role):
    radius=BASE_RADIUS[role]
    profiles=[Plane.XY.offset(z) * RegularPolygon(radius * factor,8,rotation=22.5) for z,factor in PLINTH]
    return loft(profiles,ruled=True)

def union_all(shapes):
    return shapes[0].fuse(*shapes[1:]).clean() if len(shapes)>1 else shapes[0]

def facade_channels(body,width,depth,z,height,columns):
    cuts=[]
    for i in range(columns):
        x=(i-(columns-1)/2)*WINDOW_PITCH
        for side in (-1,1):
            cuts.append(slab(GROOVE_WIDTH,GROOVE_DEPTH*2,z,height,x,side*depth/2))
    return body.cut(*cuts).clean()

@lru_cache(maxsize=None)
def build_king():
    shoulders=[rectangular_shoulder(19,16,4,25,22,8),
               rectangular_shoulder(3.2,3.2,77,9,3.2,81)]
    body=union_all([plinth('king')]+[slab(*t) for t in KING_TIERS]+[slab(*KING_CROSS),slab(*KING_CROSS_STEM)]+shoulders)
    # Empire State's long central shaft rises above a broad sequence of setbacks.
    body=facade_channels(body,16,14,37,23,3)
    body=facade_channels(body,20,17,27,6,3)
    return body

@lru_cache(maxsize=None)
def build_queen():
    from math import sin,cos,pi
    fans=[]
    for index,(r,cz,bottom,depth) in enumerate(QUEEN_FANS):
        # Four solid overlapping arch volumes create the Chrysler crown in relief
        # and silhouette, replacing a plain pointed roof with engraved arcs.
        pts=[(-r,bottom-cz),(r,bottom-cz)]+[(r*cos(i*pi/36),r*sin(i*pi/36)) for i in range(37)]
        fan=Pos(0,depth/2,cz)*extrude(Plane.XZ*Polygon(*pts,align=None),amount=depth,dir=(0,-1,0))
        cuts=[]
        angles=[30,60,90,120,150] if index==0 else [50,90,130] if index==1 else [90] if index==2 else []
        tip,base,half=(r-1.75,r-4.5,1.05) if index==0 else (r-1.5,r-3.7,.9) if index==1 else (r-1.4,r-3.4,.8)
        for degrees in angles:
            a=degrees*pi/180
            tri=[(tip*cos(a),tip*sin(a)),(base*cos(a)-half*sin(a),base*sin(a)+half*cos(a)),(base*cos(a)+half*sin(a),base*sin(a)-half*cos(a))]
            window=extrude(Plane.XZ*Polygon(*tri,align=None),amount=GROOVE_DEPTH*2,dir=(0,-1,0))
            for side in (-1,1):
                cuts.append(Pos(0,side*depth/2+GROOVE_DEPTH,cz)*window)
        fans.append(fan.cut(*cuts).clean() if cuts else fan)
    shoulders=[rectangular_shoulder(19,16,4,23,21,8),
               rectangular_shoulder(18,16,44,20,16,47)]
    body=union_all([plinth('queen')]+[slab(*t) for t in QUEEN_TIERS]+fans+[slab(3.2,3.2,70.5,5.5)]+shoulders)
    body=facade_channels(body,18,17,22,22,3)
    return body

@lru_cache(maxsize=None)
def build_bishop():
    from math import atan2,degrees
    def wedge(scale,height,z):
        # Explicit +Z extrusion: this perimeter is clockwise when viewed above.
        return Pos(0,0,z)*extrude(Polygon(*[(x*scale,y*scale) for x,y in BISHOP_POLY],align=None),amount=height,dir=(0,0,1))
    def wedge_shoulder(s0,z0,s1,z1):
        return loft([Plane.XY.offset(z)*Polygon(*[(x*s,y*s) for x,y in BISHOP_POLY],align=None)
                     for s,z in ((s0,z0),(s1,z1))],ruled=True)
    tiers=[wedge(s,h,z) for s,z,h in BISHOP_TIERS]
    # Broad perimeter cornice and a narrow prow expose the Flatiron wedge.
    cap=Pos(0,2.5,BISHOP_CAP_Z)*extrude(Plane.XZ*Polygon((-2.3,0),(4.3,0),(3.3,7),(-1.3,7),align=None),amount=5,dir=(0,-1,0))
    body=union_all([plinth('bishop')]+tiers+[cap,wedge_shoulder(.8,4,1,8),wedge_shoulder(.94,52,1.04,54)])
    cuts=[]
    main=[(x*.94,y*.94) for x,y in BISHOP_POLY]
    for a,b in [(main[1],main[2]),(main[3],main[0])]:
        dx,dy=b[0]-a[0],b[1]-a[1]
        for f in (.18,.38,.58,.78):
            cuts.append(Pos(a[0]+dx*f,a[1]+dy*f,19)*Rot(0,0,degrees(atan2(dy,dx)))*Box(1.4,1.3,32,align=(Align.CENTER,Align.CENTER,Align.MIN)))
    for z in (25,36,47):
        outer=wedge(1.02,1.3,z)
        inner=wedge_shoulder(.885,z-.1,.94,z+1.3)
        cuts.append(outer.cut(inner))
    # Bounded diagonal recess in a planar face: no thin cone-edge lip.
    groove=Pos(1,-2.5,61)*Rot(0,28,0)*Box(1.8,1.6,4)
    return body.cut(*(cuts+[groove])).clean()

@lru_cache(maxsize=None)
def build_knight():
    horse=Pos(0,KNIGHT_DEPTH/2,9)*extrude(Plane.XZ*Polygon(*KNIGHT_POLY,align=None),amount=KNIGHT_DEPTH,dir=(0,-1,0))
    body=union_all([plinth('knight'),slab(18,16,8,13),horse,
                    rectangular_shoulder(18,16,14,20,16,17)])
    cuts=[]
    for side in (-1,1):
        eye=Plane.XZ*Polygon((0,-1.8),(1.6,0),(0,2.1),(-1.6,0),align=None)
        cuts.append(Pos(4,side*KNIGHT_DEPTH/2+.7,49)*extrude(eye,amount=1.4,dir=(0,-1,0)))
        cuts.append(slab(1.6,1.6,24,14,-6,side*KNIGHT_DEPTH/2))
    return body.cut(*cuts).clean()

@lru_cache(maxsize=None)
def build_rook():
    towers=[slab(6,6,47,5,x,y) for x in (-9,9) for y in (-8,8)]
    shoulders=[rectangular_shoulder(17,15,4,21,19,8),
               rectangular_shoulder(21,19,41,24,22,44)]
    body=union_all([plinth('rook'),slab(*ROOK_BODY),slab(*ROOK_CROWN)]+towers+shoulders)
    # Twin pointed Gothic bridge portals are blind recesses; the rear web supports the roof.
    portal=[(-2.2,0),(2.2,0),(2.2,18),(0,22),(-2.2,18)]
    cuts=[]
    for x in (-4.7,4.7):
        for side in (-1,1):
            cuts.append(Pos(x,side*9.5+1.5,17)*extrude(Plane.XZ*Polygon(*portal,align=None),amount=3,dir=(0,-1,0)))
    return body.cut(*cuts).clean()

@lru_cache(maxsize=None)
def build_pawn():
    tank=Pos(0,0,PAWN_TANK_Z)*Cylinder(PAWN_TANK_R,PAWN_TANK_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    roof=Pos(0,0,PAWN_TANK_Z+PAWN_TANK_H-0.1)*Cone(PAWN_TANK_R,PAWN_TIP_R,PAWN_ROOF_H+0.1,align=(Align.CENTER,Align.CENTER,Align.MIN))
    # Continuous tapered shoulder supports tank instead of miniature struts.
    shoulder=Pos(0,0,17)*Cone(5.4,PAWN_TANK_R,5,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return union_all([plinth('pawn'),slab(*PAWN_STEM),shoulder,tank,roof])

BUILDERS=dict(king=build_king,queen=build_queen,bishop=build_bishop,knight=build_knight,rook=build_rook,pawn=build_pawn)

@lru_cache(maxsize=None)
def build_dark_tile():
    return chamfered_square(SQUARE-TILE_GAP,POCKET_CORNER,0,TILE_H)

def chamfered_square(width,corner,z,height):
    # Corner bridges keep diagonal dark-square wells from sharing a nonmanifold edge.
    h=width/2
    return profile([(-h+corner,-h),(h-corner,-h),(h,-h+corner),(h,h-corner),
                    (h-corner,h),(-h+corner,h),(-h,h-corner),(-h,-h+corner)],height,z)

def panel_well(x,y):
    # Preserve internal diagonal bridges but remove tapering wedges at panel seams.
    h=SQUARE/2
    c=POCKET_CORNER
    points=[]
    for (cx,cy),bevel in [
        ((-h,-h),[(-h,-h+c),(-h+c,-h)]),
        ((h,-h),[(h-c,-h),(h,-h+c)]),
        ((h,h),[(h,h-c),(h-c,h)]),
        ((-h,h),[(-h+c,h),(-h,h-c)]),
    ]:
        on_seam=any(abs(v-edge)<1e-8 for v in (x+cx,y+cy) for edge in (0,PANEL))
        points.extend([(cx,cy)] if on_seam else bevel)
    return Pos(x,y,0)*profile(points,BOARD_H,SEAT_Z)

def line(x1,y1,x2,y2,width=LINE_W):
    from math import atan2,degrees,hypot
    return Pos((x1+x2)/2,(y1+y2)/2,RELIEF_Z)*Rot(0,0,degrees(atan2(y2-y1,x2-x1)))*Box(hypot(x2-x1,y2-y1)+width,width,RELIEF_H,align=(Align.CENTER,Align.CENTER,Align.MIN))

def icon(kind):
    # Original relief compositions, translated from sourced cultural/urban forms.
    bits=[]
    if kind=='chinatown':
        for x in (-11,0,11):
            bits += [slab(9,12,RELIEF_Z,RELIEF_H,x,0)]
        # Recessed upper balconies and a bent street trace, not generic pagoda imagery.
        body=union_all(bits)
        cuts=[slab(6,3,RELIEF_Z+0.55,3,x,y) for x in (-11,0,11) for y in (-2.5,2.5)]
        body=body.cut(*cuts)
        return union_all([body,line(-16,-9,-3,-9),line(-3,-9,4,-6),line(4,-6,16,-6)])
    if kind=='staten':
        hull=[(-17,-4),(17,-4),(12,-8),(-12,-8)]
        bits=[profile(hull,RELIEF_H,RELIEF_Z),slab(25,5,RELIEF_Z,RELIEF_H,0,0),slab(18,3,RELIEF_Z,RELIEF_H,0,4),slab(3,3,RELIEF_Z,RELIEF_H,-4,7)]
        bits += [line(-15,-10,-2,-10),line(2,-10,15,-10)]
    elif kind=='williamsburg':
        bits=[slab(29,10,RELIEF_Z,RELIEF_H,0,-2),slab(3.5,18,RELIEF_Z,RELIEF_H,12,1)]
        body=union_all(bits)
        cuts=[]
        for x in (-10,-3,4):
            cuts.append(slab(3.5,4,RELIEF_Z+0.55,3,x,-2))
            cuts.append(Pos(x,0,RELIEF_Z+0.55)*Cylinder(1.75,3,align=(Align.CENTER,Align.CENTER,Align.MIN)))
        return body.cut(*cuts).clean()
    elif kind=='bronx':
        bits=[slab(36,15,RELIEF_Z,0.55)]
        for x in (-10,10):
            for r in (6.5,3.8):
                ring=Circle(r)-Circle(r-LINE_W)
                bits.append(Pos(x,0,RELIEF_Z)*extrude(ring,amount=RELIEF_H))
            bits.append(slab(2,2,RELIEF_Z,RELIEF_H,x,0))
        bits += [line(-3,-5,-3,4),line(3,5,3,-4)]
    elif kind=='queens':
        bits=[line(-17,4,17,4),line(-17,7,17,7),line(-17,-7,17,-7)]
        for x in (-14,-7,0,7,14):
            bits += [line(x,-7,x,4)]
        bits += [slab(12,4,RELIEF_Z,RELIEF_H,-5,9),slab(12,4,RELIEF_Z,RELIEF_H,9,9)]
    return union_all(bits)

@lru_cache(maxsize=None)
def build_panel(qx,qy):
    # Panels all print flat; coordinates recentered locally at their quadrant origin.
    body=Pos(PANEL/2,PANEL/2,0)*Box(PANEL,PANEL,BOARD_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cuts=[]
    for file in range(qx*4,qx*4+4):
        for rank in range(qy*4,qy*4+4):
            if (file+rank)%2==0:
                x=FRAME+SQUARE*(file+0.5)-qx*PANEL
                y=FRAME+SQUARE*(rank+0.5)-qy*PANEL
                cuts.append(panel_well(x,y))
    body=body.cut(*cuts).clean()
    relief=[]
    for kind,x,y,angle in GLYPH_CENTERS:
        if int(x//PANEL)==qx and int(y//PANEL)==qy:
            relief.append(Pos(x-qx*PANEL,y-qy*PANEL,0)*Rot(0,0,angle)*icon(kind))
    # Continuous inset border rails join the motifs into one civic frieze.
    gx,gy=qx*PANEL,qy*PANEL
    for global_y in (3,381):
        if gy<=global_y<gy+PANEL:
            relief.append(line(2,global_y-gy,PANEL-2,global_y-gy))
    for global_x in (3,381):
        if gx<=global_x<gx+PANEL:
            relief.append(line(global_x-gx,2,global_x-gx,PANEL-2))
    return union_all([body]+relief)
