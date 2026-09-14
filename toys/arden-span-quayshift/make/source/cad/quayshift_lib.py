"""QUAYSHIFT parametric solids. Arden completed design; cabin narrowed after finger proof.
All architecture stays in reserved cells, upright in play. No stacking or captive joints.
"""
import json, math
from pathlib import Path
from functools import lru_cache
from build123d import *
PITCH=32.0
BOARD=184.0
MARGIN=12.0
FLOOR=4.0
INSET=.4
FERRY_RADIUS=13.0
FERRY_HEIGHT=20.0
CABIN_WIDTH=12.0
CABIN_LENGTH=18.0
PORTAL_DEPTH=12.0
PORTAL_Y=19.6
HIGH_SPRING=28.0
COLORS={'A':'d5c7aa','B':'b96843','C':'d5c7aa','D':'707348','E':'b96843','F':'d5c7aa','G':'707348','H':'b96843','tray':'174b5b','ferry':'d9a53d'}
FOOTPRINTS={'A':[(0,0),(2,0)],'B':[(0,0),(2,0)],'C':[(0,0),(2,0)],'D':[(0,0),(1,0),(0,1)],'E':[(0,0),(1,0)],'F':[(0,0),(1,0)],'G':[(0,0)],'H':[(0,0)]}

def box(x,y,z,dx,dy,dz):
    return Pos(x,y,z)*Box(dx,dy,dz,align=(Align.MIN,Align.MIN,Align.MIN))

def colorize(s,name):
    s.label=name.lower()
    h=COLORS[name];s.color=Color(*[int(h[i:i+2],16)/255 for i in (0,2,4)])
    return s

def arch_cut(cx,y,z,r,jamb,depth):
    c=Pos(cx,y,z+jamb)*Rot(90,0,0)*Cylinder(r,depth,align=(Align.CENTER,Align.CENTER,Align.MAX))
    return c+box(cx-r,y,z-1,2*r,depth,jamb+1) if jamb else c

def house(x,y,w,d,h,open_front=False,door_z=16):
    # Broad volumes, deep openings, terrace roof. Rear remains planar for arch print stance.
    s=box(x,y,4,w,d,h-4)
    roof=box(x+2.4,y+(-.1 if open_front else 2.4),h-4,w-4.8,d-2.3 if open_front else d-4.8,5)
    door_height=min(15,h-4-door_z-2.4)
    cuts=[roof,arch_cut(x+w/2,y-.1,door_z,3.5,max(1,door_height-3.5),3.1)]
    for z in range(max(38,int(door_z+24)),int(h-14),23):
        for xx in ([x+w/2] if w<22 else [x+w*.28,x+w*.72]):
            cuts.append(arch_cut(xx,y-.1,z,3,8,3.1))
    if d>20:
        cuts.append(box(x-.1,y+d*.4,14,3.1,6,12))
    return s-cuts

def steps(x,y,w,n=5,rise=4,tread=4):
    # Each tread ends at the next riser; final tread meets landing at matching height.
    return box(x,y,4,w,tread,n*0+rise).fuse(*[box(x,y+i*tread,4,w,tread,(i+1)*rise) for i in range(1,n)])

def bridge(name):
    high=name!='C';deck=50 if high else 24
    slab=box(.4,PORTAL_Y,0,95.2,PORTAL_DEPTH,deck)
    slab=slab-arch_cut(48,PORTAL_Y-.1,0,16,HIGH_SPRING if high else 0,PORTAL_DEPTH+.2)
    heights={'A':(74,58),'B':(56,80),'C':(30,48)}[name]
    blocks=[]
    for i,h in zip((0,2),heights):
        x=i*PITCH
        blocks += [box(x+.4,.4,0,31.2,31.2,4),house(x+2,9.6,27.6,22,h,True)]
        # Wide three-step porch meeting a12-high landing; entirely inside each foot.
        blocks += [steps(x+8,.4,16,3,4,3.2)]
    s=slab.fuse(*blocks)
    # Low side parapets flank the open bridge deck and connect to endpoint towers.
    s=s+box(31,29.2,deck,34,2.4,3)
    return s

def building(name):
    if name in 'ABC':return bridge(name)
    if name=='D':
        base=box(.4,.4,0,63.2,31.2,4)+box(.4,31.6,0,31.2,32,4)
        return base+house(2,24,27.6,39.6,70)+house(31.6,14,30,17.6,36,True)+steps(35.6,.4,18,7,4,2)+box(35.6,14.4,4,18,4,28)
    if name in 'EF':
        h1,h2=(62,38) if name=='E' else (46,58)
        return box(.4,.4,0,63.2,31.2,4)+house(2,9.6,27.6,22,h1)+house(34,19.6,27.6,12,h2,False,24)+steps(39,.4,16,5,4,3.84)
    h=84 if name=='G' else 64
    return box(.4,.4,0,31.2,31.2,4)+house(2,9.6,27.6,22,h)+steps(8,.4,16,3,4,3.2)

def ferry():
    # Low ferry wheelhouse on a broad tapered hull; flat stern and recessed foredeck.
    hull=Cone(11,13,3,align=(Align.CENTER,Align.CENTER,Align.MIN))+Pos(0,0,3)*Cylinder(13,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
    hull=hull-box(-20,-20,-1,40,8.5,9)
    cabin=Pos(0,0,6)*extrude(RectangleRounded(CABIN_WIDTH,CABIN_LENGTH,2),FERRY_HEIGHT-6)
    cuts=[box(-3,-9.1,12,6,1.6,4),box(-3,7.5,12,6,1.6,4),box(-6.1,-3,12,1.6,6,4),box(4.5,-3,12,1.6,6,4),box(-3,9.7,5.4,6,1.3,1)]
    return hull+cabin-cuts

GLYPHS={'A':[(0,0,2,6),(2,6,4,0),(1,2.5,3,2.5)],'B':[(0,0,0,6),(0,6,3,6),(3,6,4,4.5),(4,4.5,0,3),(0,3,4,1.5),(4,1.5,3,0),(3,0,0,0)],'C':[(4,6,0,6),(0,6,0,0),(0,0,4,0)],'D':[(0,0,0,6),(0,6,3,6),(3,6,4,4),(4,4,4,2),(4,2,3,0),(3,0,0,0)],'E':[(4,6,0,6),(0,6,0,0),(0,0,4,0),(0,3,3,3)],'1':[(1,5,2,6),(2,6,2,0),(0,0,4,0)],'2':[(0,6,4,6),(4,6,4,3),(4,3,0,3),(0,3,0,0),(0,0,4,0)],'3':[(0,6,4,6),(4,6,4,0),(0,3,4,3),(0,0,4,0)],'4':[(0,6,0,3),(0,3,4,3),(4,6,4,0)],'5':[(4,6,0,6),(0,6,0,3),(0,3,4,3),(4,3,4,0),(4,0,0,0)]}

def glyph(ch,x,y,z):
    solids=[]
    for x1,y1,x2,y2 in GLYPHS[ch]:
        dx,dy=x2-x1,y2-y1;l=math.hypot(dx,dy)
        solids.append(Pos(x+x1,y+y1,z)*Rot(0,0,math.degrees(math.atan2(dy,dx)))*box(0,-.45,0,l,.9,.5))
    return solids[0].fuse(*solids[1:])

def tray():
    s=box(0,0,0,BOARD,BOARD,FLOOR)
    s=s+box(0,0,FLOOR,12,184,8)+box(172,0,FLOOR,12,184,8)
    for y in (0,172):
        s=s+box(12,y,FLOOR,64,12,8)+box(108,y,FLOOR,64,12,8)
    cuts=[]
    for i in range(1,5):
        cuts += [box(12+i*32-.175,12,3.75,.35,160,.3),box(12,12+i*32-.175,3.75,160,.35,.3)]
    for i,ch in enumerate('ABCDE'):
        cuts.append(glyph(ch,26+32*i,3,3.6 if ch=='C' else 11.6))
    for i,ch in enumerate('12345'):cuts.append(glyph(ch,4,25+32*i,11.6))
    return s-cuts

@lru_cache(maxsize=10)
def part(name):
    s=tray() if name=='tray' else ferry() if name=='ferry' else building(name)
    assert len(s.solids())==1,(name,len(s.solids()))
    return colorize(s,name)

def print_part(name):
    s=part(name).moved(Location())
    if name in 'ABC':
        s=Rot(-90,0,0)*s
        bb=s.bounding_box();s=Pos(-bb.min.X,-bb.min.Y,-bb.min.Z)*s
    return colorize(s,name)

def transformed(name,origin,rotation):
    cells=FOOTPRINTS[name]+([(1,0)] if name in 'ABC' else [])
    pts=[]
    for x,y in cells:
        for xx,yy in [(x*32,y*32),((x+1)*32,(y+1)*32)]:
            a=math.radians(rotation);pts.append((round(xx*math.cos(a)-yy*math.sin(a),8),round(xx*math.sin(a)+yy*math.cos(a),8)))
    dx,dy=-min(q[0] for q in pts),-min(q[1] for q in pts)
    return Pos(12+origin[0]*32+dx,12+origin[1]*32+dy,FLOOR)*Rot(0,0,rotation)*part(name)

def layout_data(index=1):
    return json.loads((Path(__file__).parent/'layouts.json').read_text())[index]

def assemble(index=1,ferry_xy=None):
    row=layout_data(index)
    shapes=[part('tray')]
    for p in row['placements']:
        shapes.append(colorize(transformed(p['part'],p['origin'],p['rotation']),p['part']))
    xy=ferry_xy or (92,28)
    shapes.append(colorize(Pos(xy[0],xy[1],FLOOR)*part('ferry'),'ferry'))
    return Compound(label='QUAYSHIFT',children=shapes)
