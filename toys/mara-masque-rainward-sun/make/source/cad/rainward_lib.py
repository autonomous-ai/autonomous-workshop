"""Original Rainward Sun geometry; dimensions from reviewed rainward_spec.md."""
from math import sin, cos, radians, sqrt
from functools import lru_cache
from build123d import *

# [specified] Wish dimensions; [assumed] remaining values from inventor handoff.
SUN_R, RAY_R, RAY_COUNT = 90.0, 5.0, 16
DECK, BAR_TOP, CREST_TOP, BAR_R = 16.0, 24.0, 28.0, 24.0
LANES, START_ANGLE, PITCH = 24, -75.0, 15.0
RADII = (85.,72.,59.,46.,33.)
DROP_H, DROP_L, DROP_W = 4.,12.,8.
CHANNEL_START, CHANNEL_END, CHANNEL_DEPTH = 27.,88.,0.6
CHANNEL_W, BANK_W = 2.,3.
DIE_EDGE, CUP_OD, CUP_ID, CUP_H, CUP_FLOOR = 16.,42.,38.,28.,2.
BAR_HIT_R = 85. - sqrt(80.**2-(BAR_TOP-DECK)**2)
SINGLE = [(-6,-1),(-6,1),(-2,2),(0,4),(3,4),(6,2),(6,-2),(3,-4),(0,-4),(-2,-2)]
FORK = [(-6,-3),(-6,-1),(-2,-1),(-2,1),(-6,1),(-6,3),(-2,3),(0,4),(3,4),(6,2),(6,-2),(3,-4),(0,-4),(-2,-3)]
SUN_COLOR=(1.,.66,.18)
SINGLE_COLOR=(.97,.94,.82)
FORK_COLOR=(.24,.16,.12)
CUP_COLOR=(.78,.29,.12)
DIE_COLOR=(.98,.97,.92)

def xy(r,a):
    return (r*cos(radians(a)), r*sin(radians(a)))

def theta(p):
    return START_ANGLE+PITCH*(p-1)

def finish(s,label,color):
    assert len(s.solids())==1, label
    s.label=label
    s.color=Color(*color)
    return s

def prism(points,height):
    return extrude(Polygon(*points,align=None),amount=height,dir=(0,0,1))

@lru_cache(maxsize=None)
def sun():
    base=Cylinder(SUN_R,DECK,align=(Align.CENTER,Align.CENTER,Align.MIN))
    rays=[Pos(*xy(SUN_R,k*360/RAY_COUNT),0)*Cylinder(RAY_R,DECK,align=(Align.CENTER,Align.CENTER,Align.MIN)) for k in range(RAY_COUNT)]
    base=base.fuse(*rays)
    cutters=[]
    for p in range(1,LANES+1):
        width=BANK_W if p%6==1 else CHANNEL_W
        channel=Pos((CHANNEL_START+CHANNEL_END)/2,0,DECK-CHANNEL_DEPTH)*Box(CHANNEL_END-CHANNEL_START,width,CHANNEL_DEPTH+1,align=(Align.CENTER,Align.CENTER,Align.MIN))
        cutters.append(Rot(Z=theta(p)-PITCH/2)*channel)
    base=base.cut(*cutters)
    platform=Pos(0,0,DECK)*Cylinder(BAR_R,BAR_TOP-DECK,align=(Align.CENTER,Align.CENTER,Align.MIN))
    # Blunt far-side flare lobes, outside all six rectangular bar positions.
    crest1=Pos(-7,18,DECK)*prism([(-5,-3),(4,-3),(5,2),(2,5),(-1,4),(-4,1)],CREST_TOP-DECK)
    crest2=Pos(8,18,DECK)*prism([(-4,-3),(4,-3),(4,1),(1,5),(-2,3)],CREST_TOP-DECK)
    base=base.fuse(platform,crest1,crest2)
    return finish(base,'sun',SUN_COLOR)

@lru_cache(maxsize=None)
def drop(kind):
    return finish(prism(SINGLE if kind=='single' else FORK,DROP_H),kind,SINGLE_COLOR if kind=='single' else FORK_COLOR)

@lru_cache(maxsize=None)
def cup():
    outer=Cylinder(CUP_OD/2,CUP_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cavity=Pos(0,0,CUP_FLOOR)*Cylinder(CUP_ID/2,CUP_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return finish(outer-cavity,'cup',CUP_COLOR)

@lru_cache(maxsize=None)
def die():
    # Equal, solid, plane-faced cube. Required thin ink numbering is a finishing operation.
    return finish(Box(DIE_EDGE,DIE_EDGE,DIE_EDGE,align=(Align.CENTER,Align.CENTER,Align.MIN)),'die',DIE_COLOR)

INITIAL_A={24:2,13:5,8:3,6:5}
INITIAL_B={1:2,12:5,17:3,19:5}
BEFORE_A={24:2,13:4,8:2,7:2,6:5}
BEFORE_B={1:1,2:1,12:4,17:3,18:1,19:5}

def piece_poses(state='setup'):
    a,b=(INITIAL_A,INITIAL_B) if state=='setup' else (BEFORE_A,BEFORE_B)
    out={}
    for kind,counts in [('single',a),('fork',b)]:
        i=0
        for p,n in sorted(counts.items()):
            for j in range(n):
                i+=1
                x,y=xy(RADII[j%5],theta(p))
                out[f'{kind}_{i:02d}']=(kind,p,(x,y,DECK+(j//5)*DROP_H),theta(p))
    if state=='after':
        attacker=next(k for k,v in out.items() if v[0]=='single' and v[1]==7)
        victim=next(k for k,v in out.items() if v[0]=='fork' and v[1]==1)
        out[attacker]=('single',1,out[victim][2],theta(1))
        out[victim]=('fork',0,(*xy(BAR_HIT_R,theta(1)),BAR_TOP),theta(1))
    assert len(out)==30
    return out

def assembly(state='setup'):
    pieces=[sun().moved(Location())]
    for name,(kind,p,pos,angle) in piece_poses(state).items():
        piece=Pos(*pos)*Rot(Z=angle)*drop(kind)
        piece.label=name
        pieces.append(piece)
    for i,x in enumerate((-120.,120.),1):
        part=Pos(x,25,0)*cup(); part.label=f'cup_{i}';pieces.append(part)
    for i,x in enumerate((-15.,15.),1):
        part=Pos(x,-115,0)*die(); part.label=f'die_{i}';pieces.append(part)
    return Compound(label='rainward_sun',children=pieces)
