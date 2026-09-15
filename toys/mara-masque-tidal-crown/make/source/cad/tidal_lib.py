"""Text-derived Mara design; dimensions mm, XY bed at Z0. No bought parts."""
from build123d import *
import math
from shapely.geometry import LineString, Polygon as SPolygon, box
from shapely.ops import unary_union
from scipy.interpolate import splprep, splev

BOARD_SIZE=196.0
BOARD_HEIGHT=12.0
CELL=18.0
BASE_D=14.0
BASE_H=3.0
BLACK_WIDTH=11.6
BLACK_RADIUS=3.0
HEIGHTS=dict(pawn=12,rook=18,knight=21,bishop=23,queen=26,king=28)
COLORS=dict(board=(0.23,0.36,0.43),white=(0.94,0.86,0.69),black=(0.22,0.25,0.30))

def slab(points,z,h):
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))
    points=points if area>0 else list(reversed(points))
    return Pos(0,0,z)*extrude(Polygon(*points,align=None),amount=h)

def profile_xz(points,thick=5):
    return extrude(Plane.XZ*Polygon(*points,align=None),amount=thick/2,both=True)

def cylinder(r,z,h):
    return Pos(0,0,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))

def cone(r1,r2,z,h):
    return Pos(0,0,z)*Cone(r1,r2,h,align=(Align.CENTER,Align.CENTER,Align.MIN))

def base(side):
    face=Circle(BASE_D/2) if side=='white' else RectangleRounded(BLACK_WIDTH,BLACK_WIDTH,BLACK_RADIUS)
    return extrude(face,amount=BASE_H)

def finish(shape,label,side):
    shape=shape.clean()
    assert len(shape.solids())==1, label
    shape.label=label
    shape.color=Color(*COLORS[side])
    return shape

def board():
    points=[(74,-66),(86,-44),(92,-14),(88,20),(76,52),(53,77),(22,90),(-10,92)]
    tck,_=splprep(list(zip(*points)),s=0,k=3)
    xx,yy=splev([i/47 for i in range(48)],tck)
    # Normalize each centerline axis so round 6mm caps give exact196 bounds.
    xx=[x*92/max(abs(v) for v in xx) for x in xx]
    yy=[y*92/max(abs(v) for v in yy) for y in yy]
    arm=LineString(list(zip(xx,yy))).buffer(6,quad_segs=4)
    other=LineString([(-x,-y) for x,y in zip(xx,yy)]).buffer(6,quad_segs=4)
    core=box(-76,-76,76,76)
    outline=unary_union([core,arm,other])
    shape=slab(list(outline.exterior.coords)[:-1],0,BOARD_HEIGHT)
    for ring in outline.interiors:
        shape-=slab(list(ring.coords)[:-1],-1,BOARD_HEIGHT+2)
    cuts=[]
    for f in range(8):
        for r in range(8):
            if (f+r)%2==0:
                # Rounded outer corners avoid point-touching recess voids.
                outer=loft([Pos(0,0,10)*RectangleRounded(14,14,1.5),Pos(0,0,12)*RectangleRounded(18,18,3.5)],ruled=True)
                outer+=Pos(0,0,12)*extrude(RectangleRounded(18,18,3.5),amount=1)
                outer-=Pos(0,0,9)*extrude(RectangleRounded(14,14,1.5),amount=5)
                cuts.append(Pos(-63+f*CELL,-63+r*CELL,0)*outer)
    shape=shape.cut(*cuts)
    return finish(shape,'board','board')

def man(role,side):
    shape=base(side)
    if role=='pawn':
        head=cylinder(3.5,2.8,3.2)+cone(3.5,5,6,2)+cylinder(5,8,2)+cone(5,3,10,2)
    elif role=='rook':
        head=Pos(0,0,3)*Box(8,8,10,align=(Align.CENTER,Align.CENTER,Align.MIN))
        head+=loft([Pos(0,0,13)*Rectangle(8,8),Pos(0,0,14)*Rectangle(10,8)])
        head+=Pos(0,0,14)*Box(10,8,4,align=(Align.CENTER,Align.CENTER,Align.MIN))
        head-=Pos(0,0,16)*Box(4,10,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
    elif role=='knight':
        head=cylinder(4,2.8,3.2)+profile_xz([(-4,5),(3,5),(2,10),(5,14),(5,17),(2,19),(2,21),(-1,21),(-4,17),(-4,13),(-2,10)])
    elif role=='bishop':
        head=cylinder(4,2.8,7.2)+profile_xz([(-3,9),(3,9),(5,15),(5,19),(4.2,23),(-4.2,23),(-5,19),(-5,15)])
        # 2mm-wide open diagonal lane, blunt closed termination.
        dx,dz=2,5; n=math.hypot(dx,dz); ox,oz=dz/n,-dx/n
        cut=[(-1-ox,18-oz),(-1+ox,18+oz),(3+ox,28+oz),(3-ox,28-oz)]
        head-=profile_xz(cut,7)
    elif role=='queen':
        head=cylinder(4,2.8,13.2)+cone(4,6,16,2)+cylinder(6,18,3)
        # True radial spirals replace concentric sectors after independent review.
        # 2.2mm normal-width arms have measured 2.059mm mutual clearance.
        for rot in (0,180):
            pts=[]
            for i in range(25):
                a=math.radians(rot+i*5);r=2.2+2.7*i/24
                pts.append((r*math.cos(a),r*math.sin(a)))
            arm=LineString(pts).buffer(1.1,quad_segs=3).simplify(0.03,preserve_topology=True)
            head+=slab(list(arm.exterior.coords)[:-1],20,6)
    elif role=='king':
        head=cylinder(4,2.8,15.2)+Pos(0,0,18)*Box(6,6,5,align=(Align.CENTER,Align.CENTER,Align.MIN))
        head+=profile_xz([(-1.5,20),(1.5,20),(4.5,23),(4.5,26),(1.5,26),(1.5,28),(-1.5,28),(-1.5,26),(-4.5,26),(-4.5,23)],3)
    else:
        raise ValueError(role)
    return finish(shape+head,side+'_'+role,side)
