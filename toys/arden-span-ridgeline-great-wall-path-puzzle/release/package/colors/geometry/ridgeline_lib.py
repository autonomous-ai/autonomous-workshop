"""RIDGELINE parametric solids. Millimeters; local origin on underside, N=+Y.
All units are monolithic. Source revision 2: complete architectural vocabulary.
"""
from build123d import *
from math import ceil, hypot, degrees, atan2
import cadfits

PITCH = 56.0
TILE = 55.6
BASE = 4.0
FLOOR = 4.0
LEVELS = (20.0, 32.0, 44.0)
WALK = 12.0
GUARD = 2.4
GUARD_H = 3.5
MERLON_H = 3.0
WALL = WALK + 2 * GUARD
SEAM_LANDING = 4.0
RISERS = 6
RISE = 2.0
OUTER = 174.0
MATRIX_SPAN = 2*PITCH+TILE
CRADLE_OPENING = cadfits.slot_for(MATRIX_SPAN, 0.4)
LIP_H = 1.5
PORTS = {'A':{0:0,1:1},'B':{0:1,1:1},'C':{0:1,1:2},'D':{0:2,1:1},
         'S':{0:0,2:1},'T':{0:1,2:1},'U':{0:1,2:2},'G1':{0:1},'G2':{0:2}}
STONE = (247/255,230/255,222/255)
DARK = (111/255,110/255,109/255)
assert TILE < PITCH and WALK >= 12 and GUARD >= 2.4
assert LEVELS[1]-LEVELS[0] == RISERS*RISE

def box(x,y,z,dx,dy,dz):
    return Pos(x,y,z)*Box(dx,dy,dz,align=(Align.CENTER,Align.CENTER,Align.MIN))

def rectangle_at(z,dx,dy,x=0,y=0):
    return Plane(origin=(x,y,z))*Rectangle(dx,dy)

def ridge_terrain(high,ports):
    # Broad irregular facets, never taller than the low route level.
    bottom=[(-25,-22),(-12,-27),(22,-25),(27,-10),(24,24),(8,27),(-25,22),(-27,2)]
    middle=[(-17,-15),(-8,-20),(14,-16),(20,-6),(15,17),(4,20),(-19,15),(-19,0)]
    summit=[(-10,-9),(-5,-12),(8,-11),(11,-3),(10,10),(3,12),(-11,9),(-12,0)]
    if ports=={0:1,2:1}:
        # T retains exact half-turn terrain symmetry.
        bottom=[(-25,-22),(0,-27),(25,-22),(27,0),(25,22),(0,27),(-25,22),(-27,0)]
        middle=[(x*.7,y*.7) for x,y in bottom]
        summit=[(x*.4,y*.4) for x,y in bottom]
    top=high-12.0
    sections=[Plane.XY.offset(BASE-.2)*Polygon(*bottom,align=None),
              Plane.XY.offset(BASE+(top-BASE)*.58)*Polygon(*middle,align=None),
              Plane.XY.offset(top)*Polygon(*summit,align=None)]
    chunks=[loft(sections,ruled=True)]
    for d,level in ports.items():
        terrain_top=LEVELS[level]-12
        chunks.append(loft([rectangle_at(BASE-.2,33,TILE/2-10,0,(TILE/2+10)/2),
                            rectangle_at(terrain_top,21,TILE/2-10,0,(TILE/2+10)/2)],ruled=True).rotate(Axis.Z,-90*d))
    return chunks[0].fuse(*chunks[1:])

def arm_sections(low,high):
    """Ordered from central landing to seam, actual tread rectangles."""
    inside=WALK/2
    outer=TILE/2
    if low == high:
        return [(inside,outer,high)]
    stair_end=outer-SEAM_LANDING
    run=(stair_end-inside)/RISERS
    sections=[]
    for i in range(RISERS):
        # first tread outboard of central landing is already at high;
        # six risers include the one immediately after the seam landing.
        sections.append((inside+i*run,inside+(i+1)*run,high-i*RISE))
    return sections+[(stair_end,outer,low)]

def route_arm(low,high,start=WALK/2):
    chunks=[]
    for a,b,z in arm_sections(low,high):
        a=max(a,start)
        if b<=a: continue
        chunks.append(box(0,(a+b)/2,BASE-.2,WALL,b-a,z-BASE+.2))
        for sign in (-1,1):
            chunks.append(box(sign*(WALK+GUARD)/2,(a+b)/2,z,GUARD,b-a,GUARD_H))
    # Sparse strong merlons, each fully supported by the stepped parapet.
    for a,b,z in arm_sections(low,high):
        a=max(a,start)
        if b<=a: continue
        if b-a>10:
            positions=[a+2.5,b-2.5]
            length=4.4
        elif b-a>3.5:
            positions=[(a+b)/2]; length=min(4.4,b-a)
        else:
            positions=[(a+b)/2] if int(round((a-WALK/2)/((TILE/2-SEAM_LANDING-WALK/2)/RISERS)))%2 == 0 else []
            length=b-a
        for y in positions:
            for sign in (-1,1):
                chunks.append(box(sign*(WALK+GUARD)/2,y,z+GUARD_H,GUARD,length,MERLON_H))
    return chunks[0].fuse(*chunks[1:])

def central_landing(ports,high):
    chunks=[box(0,0,BASE-.2,WALL,WALL,high-BASE+.2)]
    # Opening on each actual route arm; closed wall on other sides.
    for d in range(4):
        if d not in ports:
            g=box(0,(WALK+GUARD)/2,high,WALL,GUARD,GUARD_H)
            chunks.append(g.rotate(Axis.Z,-90*d))
            for x in (-5.8,5.8):
                chunks.append(box(x,(WALK+GUARD)/2,high+GUARD_H,4.4,GUARD,MERLON_H).rotate(Axis.Z,-90*d))
    # Four robust guard corner blocks remain outside the clear walkway.
    for x in (-1,1):
        for y in (-1,1):
            chunks.append(box(x*(WALK+GUARD)/2,y*(WALK+GUARD)/2,high,GUARD,GUARD,GUARD_H))
    return chunks[0].fuse(*chunks[1:])

def module(key):
    ports=PORTS[key]
    high=LEVELS[max(ports.values())]
    chunks=[box(0,0,0,TILE,TILE,BASE),ridge_terrain(high,ports)]
    chunks.append(gate_tower(high) if key.startswith("G") else central_landing(ports,high))
    for direction,level in ports.items():
        chunks.append(route_arm(LEVELS[level],high,14 if key.startswith("G") else WALK/2).rotate(Axis.Z,-90*direction))
    chunks.append(identifier(key))
    shape=chunks[0].fuse(*chunks[1:]).clean()
    if key.startswith("G"):
        shape=shape.cut(passage_tool()).clean()
    assert len(shape.solids())==1
    shape.label=key.lower()
    shape.color=Color(*STONE)
    return shape

def placed(key,cell,rotation):
    return module(key).rotate(Axis.Z,-90*rotation).translate((PITCH*(cell%3-1),PITCH*(1-cell//3),FLOOR))

def build_state(state):
    return Compound(label='ridgeline',children=[cradle()]+[placed(key,cell,r) for cell,key,r in state])


def prism(points,direction):
    return Solid.extrude(Face(Wire.make_polygon(points,close=True)),Vector(direction))

def passage_tool():
    # True E-W passage with a self-supporting pointed crown, through mountain.
    return prism([(-29,-6,8),(-29,6,8),(-29,6,16),(-29,0,22),(-29,-6,16)],(58,0,0))

def gate_tower(deck):
    chunks=[loft([rectangle_at(BASE-.2,34,34),rectangle_at(deck,28,28)],ruled=True)]
    thick=3.2
    for d in (1,2,3):
        chunks.append(box(0,14-thick/2,deck,28,thick,12).rotate(Axis.Z,-90*d))
    for x in (-10,10): chunks.append(box(x,14-thick/2,deck,8,thick,12))
    for d in range(4):
        for x in (-11.4,0,11.4):
            if d==0 and x==0: continue
            chunks.append(box(x,14-thick/2,deck+12,5.2,thick,3).rotate(Axis.Z,-90*d))
    shape=chunks[0].fuse(*chunks[1:])
    # Pointed wall apertures; floor below each remains 3 mm thick.
    for d in (1,2,3):
        cutter=prism([(-2,10,deck+3),(2,10,deck+3),(2,10,deck+7),(0,10,deck+9),(-2,10,deck+7)],(0,5,0))
        shape=shape.cut(cutter.rotate(Axis.Z,-90*d))
    return shape

GLYPHS={
 'A':[[(0,0),(1.5,5),(3,0)],[(.6,2),(2.4,2)]],
 'B':[[(0,0),(0,5),(2.3,5),(3,4),(2.3,2.5),(0,2.5)],[(2.3,2.5),(3,1),(2.3,0),(0,0)]],
 'C':[[(3,5),(0,5),(0,0),(3,0)]],
 'D':[[(0,0),(0,5),(2,5),(3,4),(3,1),(2,0),(0,0)]],
 'S':[[(3,5),(0,5),(0,2.5),(3,2.5),(3,0),(0,0)]],
 'T':[[(0,5),(3,5)],[(1.5,5),(1.5,0)]],
 'U':[[(0,5),(0,0),(3,0),(3,5)]],
 'G':[[(3,5),(0,5),(0,0),(3,0),(3,2.5),(1.7,2.5)]],
 '1':[[(.5,4),(1.5,5),(1.5,0)],[(.3,0),(2.7,0)]],
 '2':[[(0,5),(3,5),(3,2.5),(0,2.5),(0,0),(3,0)]]}

def identifier(key):
    # Raised block strokes need no fonts and remain actual inspectable CAD.
    width=4.4*len(key)+1.6
    stroke_width=1.25 if key=="G2" else .9
    stroke_height=1.2 if key=="G2" else .8
    chunks=[box(-21,-22,0,width+1.8,8.2,8.8)]
    for n,char in enumerate(key):
        for polyline in GLYPHS[char]:
            for (x1,y1),(x2,y2) in zip(polyline,polyline[1:]):
                dx=x2-x1; dy=y2-y1
                stroke=box(0,0,8.8,hypot(dx,dy)+stroke_width,stroke_width,stroke_height)
                stroke=stroke.rotate(Axis.Z,degrees(atan2(dy,dx))).translate((-21-width/2+1.25+n*4.4+(x1+x2)/2,-24.5+(y1+y2)/2,0))
                chunks.append(stroke)
    return chunks[0].fuse(*chunks[1:])

def cradle():
    shape=box(0,0,0,OUTER,OUTER,FLOOR+LIP_H).cut(box(0,0,FLOOR,CRADLE_OPENING,CRADLE_OPENING,LIP_H+1))
    # Four broad interruptions of the low perimeter lip aid corner access.
    for d in range(4):
        shape=shape.cut(box(0,OUTER/2,FLOOR,30,8,LIP_H+1).rotate(Axis.Z,90*d))
    from cradle_grid import enhance_cradle
    shape=enhance_cradle(shape)
    shape.label='cradle'; shape.color=Color(*DARK)
    return shape.clean()
