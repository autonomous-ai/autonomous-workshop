"""Rainward Flow correction of cloned Rainward Sun; unchanged rules and datums retained."""
from math import sin, cos, radians, sqrt
from functools import lru_cache
from build123d import *
from OCP.BRep import BRep_Builder
from OCP.gp import gp_Pnt

# [specified] Wish dimensions; [assumed] remaining values from inventor handoff.
SUN_R, RAY_R, RAY_COUNT = 90.0, 5.0, 16
DECK, BAR_TOP, CREST_TOP, BAR_R = 16.0, 17.0, 17.0, 24.0
LANE_TOP, LANE_INNER, EDGE_ROUND = 16.8, 26.5, 0.15
MARKER_R, MARKER_L, MARKER_W, MARKER_TOP = 65., 10., 0.8, 17.0
LANES, START_ANGLE, PITCH = 24, -75.0, 15.0
RADII = (85.,72.,59.,46.,33.)
DROP_H, DROP_L, DROP_W = 4.,12.,8.
CHANNEL_START, CHANNEL_END, CHANNEL_DEPTH = 0.,110.,0.8
CHANNEL_W, BANK_W = 0.8,1.6
DIE_EDGE, CUP_OD, CUP_ID, CUP_H, CUP_FLOOR = 16.,42.,38.,28.,2.
BAR_HIT_R = 85. - sqrt(80.**2-(BAR_TOP-LANE_TOP)**2)
# Reviewed Mara R2: uninterrupted swept stream, terminal split only final1.3mm.
SINGLE_CURVES = [[[6, -1], [6, 0.657], [4.657, 2], [3, 2]], [[3, 2], [0.3, 2], [-2.8, 4], [-5, 4]], [[-5, 4], [-5.552, 4], [-6, 3.5296], [-6, 2.95]], [[-6, 2.95], [-6, 2.3704], [-5.552, 1.9], [-5, 1.9]], [[-5, 1.9], [-2.8, 1.9], [-0.3, -4], [3, -4]], [[3, -4], [4.657, -4], [6, -2.657], [6, -1]]]
FORK_CURVES = [[[6, -1], [6, 0.657], [4.657, 2], [3, 2]], [[3, 2], [0.3, 2], [-2.8, 4], [-5, 4]], [[-5, 4], [-5.552, 4], [-6, 3.5296], [-6, 2.95]], [[-6, 2.95], [-6, 2.3704], [-5.552, 1.9], [-5, 1.9]], [[-5, 1.9], [-4.6, 1.9], [-4.6, 1.1], [-5, 1.1]], [[-5, 1.1], [-5.552, 1.1], [-6, 0.652], [-6, 0.1]], [[-6, 0.1], [-6, -0.452], [-5.552, -0.9], [-5, -0.9]], [[-5, -0.9], [-2.8, -0.9], [-0.3, -4], [3, -4]], [[3, -4], [4.657, -4], [6, -2.657], [6, -1]]]

def sampled_outline(curves):
    points=[]
    for curve in curves:
        for i in range(64):
            t=i/64; u=1-t
            points.append(tuple(u**3*curve[0][j]+3*u*u*t*curve[1][j]+3*u*t*t*curve[2][j]+t**3*curve[3][j] for j in (0,1)))
    return points

SINGLE,FORK=sampled_outline(SINGLE_CURVES),sampled_outline(FORK_CURVES)
PIP_RADIUS,PIP_DEPTH,PIP_PITCH=1.0,1.1,4.0
PIP_LAYOUTS={1:[(0,0)],2:[(-1,-1),(1,1)],3:[(-1,-1),(0,0),(1,1)],4:[(-1,-1),(-1,1),(1,-1),(1,1)],5:[(-1,-1),(-1,1),(0,0),(1,-1),(1,1)],6:[(-1,-1),(-1,0),(-1,1),(1,-1),(1,0),(1,1)]}
PIP_FACES=[(1,(0,0,1)),(6,(0,0,-1)),(2,(1,0,0)),(5,(-1,0,0)),(3,(0,1,0)),(4,(0,-1,0))]
PIP_COLOR=(.065,.055,.05)
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

def board_blank(height):
    base=Cylinder(SUN_R,height,align=(Align.CENTER,Align.CENTER,Align.MIN))
    rays=[Pos(*xy(SUN_R,k*360/RAY_COUNT),0)*Cylinder(RAY_R,height,align=(Align.CENTER,Align.CENTER,Align.MIN)) for k in range(RAY_COUNT)]
    return base.fuse(*rays)

def separator(angle):
    # Short capsule in the wider channel, never at a point endpoint.
    marker=extrude(SlotOverall(MARKER_L,MARKER_W),amount=MARKER_TOP-DECK)
    marker=fillet(marker.edges().filter_by_position(Axis.Z,MARKER_TOP-DECK,MARKER_TOP-DECK),radius=0.3)
    return Rot(Z=angle)*Pos(MARKER_R,0,DECK)*marker

@lru_cache(maxsize=None)
def sun():
    # [specified] Preserve190x190 plan; [assumed] reviewed Lowflow relief.
    base=board_blank(LANE_TOP)
    cutters=[Pos(0,0,DECK)*Cylinder(LANE_INNER,2,align=(Align.CENTER,Align.CENTER,Align.MIN))]
    for p in range(1,LANES+1):
        width=BANK_W if p%6==1 else CHANNEL_W
        channel=Pos(CHANNEL_END/2,0,DECK)*Box(CHANNEL_END,width,2,align=(Align.CENTER,Align.CENTER,Align.MIN))
        cutters.append(Rot(Z=theta(p)-PITCH/2)*channel)
    base=base.cut(*cutters)
    edges=[e for e in base.edges().filter_by_position(Axis.Z,LANE_TOP,LANE_TOP) if e.geom_type==GeomType.LINE and e.length>50]
    base=fillet(edges,radius=EDGE_ROUND)
    platform=Pos(0,0,DECK)*Cylinder(BAR_R,BAR_TOP-DECK,align=(Align.CENTER,Align.CENTER,Align.MIN))
    base=base.fuse(platform,*[separator(theta(p)+PITCH/2) for p in (6,12,18,24)])
    return finish(base,'sun',SUN_COLOR)

def canonical_vertices(shape):
    # Normalize sub-picometer endpoint roundoff before extrusion. OCP otherwise
    # alternates the preserved0.1 endpoint across its scientific-format threshold,
    # changing STEP hashes between identical builds. Curves/features are unchanged.
    builder=BRep_Builder()
    for vertex in shape.vertices():
        xyz=(vertex.X,vertex.Y,vertex.Z)
        fixed=tuple(round(v,10) for v in xyz)
        assert max(abs(a-b) for a,b in zip(xyz,fixed))<1e-9
        builder.UpdateVertex(vertex.wrapped,gp_Pnt(*fixed),1e-7)
    return shape

@lru_cache(maxsize=None)
def drop(kind):
    curves=SINGLE_CURVES if kind=='single' else FORK_CURVES
    wire=Wire([Edge.make_bezier(*[(x,y,0) for x,y in row]) for row in curves])
    if kind=='fork': canonical_vertices(wire)
    body=extrude(Face(wire),amount=DROP_H,dir=(0,0,1))
    if kind=='fork': canonical_vertices(body)
    return finish(body,kind,SINGLE_COLOR if kind=='single' else FORK_COLOR)

@lru_cache(maxsize=None)
def cup():
    outer=Cylinder(CUP_OD/2,CUP_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cavity=Pos(0,0,CUP_FLOOR)*Cylinder(CUP_ID/2,CUP_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return finish(outer-cavity,'cup',CUP_COLOR)

@lru_cache(maxsize=None)
def die():
    body=Box(DIE_EDGE,DIE_EDGE,DIE_EDGE,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cutters=[]
    for value,normal in PIP_FACES:
        n=Vector(normal)
        center=Vector(0,0,DIE_EDGE/2)+n*(DIE_EDGE/2-PIP_DEPTH)
        plane=Plane(origin=center,x_dir=(0,1,0) if normal[0] else (1,0,0),z_dir=normal)
        for u,v in PIP_LAYOUTS[value]:
            cutters.append(plane*Pos(u*PIP_PITCH,v*PIP_PITCH,0)*Cone(0,PIP_RADIUS*(PIP_DEPTH+1)/PIP_DEPTH,PIP_DEPTH+1,align=(Align.CENTER,Align.CENTER,Align.MIN)))
    body=finish(body.cut(*cutters),'die',DIE_COLOR)
    # Exact recess surfaces receive charcoal paint. Renderer classifies these
    # native faces after STEP import; no graphics or added pip solids.
    for face in body.faces():
        if face.area<10: face.color=Color(*PIP_COLOR)
    return body

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
                out[f'{kind}_{i:02d}']=(kind,p,(x,y,LANE_TOP+(j//5)*DROP_H),theta(p))
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
    return Compound(label='rainward_lowflow',children=pieces)
