"""Original Dustlight Crossing geometry; mm, XY bed, +Z up.
Dimensions are deliberate compact assumptions from reviewed Mara handoff.
"""
from build123d import *
from math import sin, cos, pi
PITCH=30.0
BORDER=6.0
BOARD_W=222.0
BOARD_D=282.0
SURFACE=5.0
BASE_H=3.2
BASE_R=11.0
CLIP=3.0
HEIGHTS=(18.,20.,22.,24.,26.,28.,30.,32.)
NAMES=('dust_knot','asteroid','crater_moon','ringed_planet','red_dwarf','twin_tail_comet','pulsar','red_giant')
TEAM_COLORS=((.97,.90,.82),(.08,.32,.52))
PANEL_BOUNDS=((0.,0.,96.,126.),(96.,0.,222.,126.),(0.,126.,96.,282.),(96.,126.,222.,282.))
STARTS=(((6,2),(1,1),(2,2),(5,1),(4,2),(0,0),(6,0),(0,2)),((0,6),(5,7),(4,6),(1,7),(2,6),(6,8),(0,8),(6,6)))
RIVERS={(x,y) for x in (1,2,4,5) for y in (3,4,5)}
TRAPS={(2,0),(3,1),(4,0),(2,8),(3,7),(4,8)}
DENS={(3,0),(3,8)}
GROOVE=.8
DEPTH=.6
RELIEF=.65
NUM_W=3.6
NUM_H=5.0
NUM_T=.85
NUM_Y=7.5
DIGITS={0:'abcedf',1:'bc',2:'abged',3:'abgcd',4:'fgbc',5:'afgcd',6:'afgecd',7:'abc',8:'abcdefg',9:'abfgcd'}

def profile(points,z=0):
    return Pos(0,0,z)*Polygon(*points,align=None)

def round_mass(stations,sy=1.0,facets=0):
    sections=[]
    for z,r in stations:
        sk=RegularPolygon(r,facets) if facets else Ellipse(r,r*sy)
        sections.append(Pos(0,0,z)*sk)
    return loft(sections,ruled=True)

def digit(n,w=NUM_W,h=NUM_H,t=NUM_T,depth=RELIEF):
    pos={'a':(0,h/2,w,t),'g':(0,0,w,t),'d':(0,-h/2,w,t),
         'f':(-w/2,h/4,t,h/2),'b':(w/2,h/4,t,h/2),
         'e':(-w/2,-h/4,t,h/2),'c':(w/2,-h/4,t,h/2)}
    boxes=[Pos(x,y,depth/2)*Box(dx,dy,depth) for k in DIGITS[n] for x,y,dx,dy in [pos[k]]]
    return Compound(children=boxes)

def base(team,rank):
    if team==0:
        s=Cylinder(BASE_R,BASE_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    else:
        r=BASE_R;c=CLIP
        pts=[(-r+c,-r),(r-c,-r),(r,-r+c),(r,r-c),(r-c,r),(-r+c,r),(-r,r-c),(-r,-r+c)]
        s=extrude(profile(pts),BASE_H)
    # Numerals live on opposite exposed aprons; no font dependency.
    for angle in (0,180):
        marks=Pos(0,0,BASE_H-.15)*Rot(0,0,angle)*Pos(0,-NUM_Y,0)*digit(rank)
        s=s.fuse(*marks.solids())
    return s

def dust():
    a=round_mass([(3,4.3),(6,5.3),(9,5.8),(11,5.7),(13,5.2),(15,4.3),(17,2.8),(18,1.8)])
    b=Pos(-3.7,1.2,0)*round_mass([(3,3.3),(7,4.1),(9,4.0),(11,3.6),(12.5,2.9),(13.5,2.0)])
    c=Pos(3.6,1.8,0)*round_mass([(3,2.8),(6,3.6),(8,3.7),(10,3.1),(11,2.6),(12,1.8)])
    return a.fuse(b,c)

def asteroid():
    sections=[Pos(x,0,z)*RegularPolygon(r,7,rotation=a) for z,r,x,a in [(3,4.8,0,0),(10,7.6,-.8,9),(16,6.0,.5,18),(20,3.8,.2,12)]]
    s=loft(sections,ruled=True)
    cuts=[Pos(x,-7.2,z)*extrude(Plane.XZ*Polygon((0,-r),(r,0),(0,r),(-r,0)),2.0,dir=(0,1,0)) for x,z,r in [(-2,12,1.4),(2.2,15,1.1),(2,9,1.)]]
    return s.cut(*cuts)

def moon():
    s=round_mass([(3,4.5),(9,8),(15,8),(20,5.5),(22,2.5)],sy=.55)
    crater=Pos(2,-4.7,14)*extrude(Plane.XZ*Polygon((0,-2.5),(2.5,0),(0,2.5),(-2.5,0)),1.8,dir=(0,1,0))
    terminator=Pos(-5,-4.7,13)*extrude(Plane.XZ*Polygon((-.5,-3.5),(.5,-3.5),(.5,3),(0,3.5),(-.5,3)),1.8,dir=(0,1,0))
    return s.cut(crater,terminator)

def planet():
    return round_mass([(3,4.5),(8,5),(11,7),(13,9),(14.6,9),(16,7),(20,6),(23,3),(24,1.8)],sy=.70)

def dwarf():
    points=[((7.6 if i%2==0 else 6.1)*cos(i*pi/8),(7.6 if i%2==0 else 6.1)*sin(i*pi/8)) for i in range(16)]
    return loft([Pos(0,0,z)*Polygon(*[(x*scale,y*scale) for x,y in points],align=None) for z,scale in [(3,.58),(10,.65),(16,1),(20,.95),(26,.25)]],ruled=True)

def comet():
    body=Pos(-2,0,0)*round_mass([(3,4.8),(9,5.5),(14,4.8),(18,2.8)],sy=.8)
    # Two thick fins emerge from the same root, separated at their blunt ends.
    tails=[]
    for pts in [[(-2,8),(3,10),(6.7,28),(4.2,28)], [(-4,8),(-1,10),(1.1,24),(-1.5,24)]]:
        tails.append(Pos(0,-2.1,0)*extrude(Plane.XZ*Polygon(*pts,align=None),4.2,dir=(0,1,0)))
    return body.fuse(*tails)

def pulsar():
    return round_mass([(3,4.5),(7,3.0),(12,5.5),(15,7.5),(16.5,7.5),(19,5),(23,3),(29,1.8),(30,1.8)],sy=.72,facets=8)

def giant():
    points=[((8.8 if i%2==0 else 8.1)*cos(i*pi/12),(8.8 if i%2==0 else 8.1)*sin(i*pi/12)) for i in range(24)]
    return loft([Pos(0,0,z)*Polygon(*[(x*scale,y*scale) for x,y in points],align=None) for z,scale in [(3,.51),(9,.56),(16,.83),(23,1),(28,.83),(32,.38)]],ruled=True)

BUILDERS=(dust,asteroid,moon,planet,dwarf,comet,pulsar,giant)
def piece(team,rank):
    s=base(team,rank).fuse(BUILDERS[rank-1]())
    assert len(s.solids())==1
    s.label=('circle_' if team==0 else 'square_')+NAMES[rank-1]
    s.color=Color(*TEAM_COLORS[team])
    return s

def panel(index):
    x0,y0,x1,y1=PANEL_BOUNDS[index]
    s=Box(x1-x0,y1-y0,SURFACE,align=(Align.MIN,Align.MIN,Align.MIN))
    cutters=[]
    def slot(x,y,w,d):
        # all decoration recesses are in integral top, with >=4.4 mm backing
        cutters.append(Pos(x-x0,y-y0,SURFACE-DEPTH/2)*Box(w,d,DEPTH))
    for x in [BORDER+PITCH*i for i in range(8)]:
        if x0 < x < x1:slot(x,(y0+y1)/2,GROOVE,y1-y0)
    for y in [BORDER+PITCH*i for i in range(10)]:
        if y0 < y < y1:slot((x0+x1)/2,y,x1-x0,GROOVE)
    # Batch grid first, then independently spaced terrain strokes.
    s=s.cut(*cutters);cutters=[]
    for cy in range(9):
      for cx in range(7):
        x=BORDER+PITCH*(cx+.5);y=BORDER+PITCH*(cy+.5)
        if not(x0<x<x1 and y0<y<y1):continue
        if (cx,cy) in RIVERS:
            for d in (-13.2,13.2):slot(x,y+d,23,1.0)
            for d in (-13.2,13.2):slot(x+d,y,1.0,22)
        elif (cx,cy) in TRAPS:
            for dx,dy,w,h in [(-12.9,0,1.2,8),(12.9,0,1.2,8),(0,-12.9,8,1.2),(0,12.9,8,1.2)]:slot(x+dx,y+dy,w,h)
        elif (cx,cy) in DENS:
            # Single aperture outline: no fragile parallel ridge.
            d=13.2
            for dx,dy,w,h in [(0,-d,2*d+1,1),(0,d,2*d+1,1),(-d,0,1,2*d),(d,0,1,2*d)]:slot(x+dx,y+dy,w,h)
    # Team ownership marks in the border beside the two dens.
    for cy,team in [(3.,0),(279.,1)]:
        if x0<111<x1 and y0<cy<y1:
            if team==0: mark=extrude(Circle(2.2)-Circle(1.2),DEPTH)
            else: mark=extrude(Rectangle(4.4,4.4)-Rectangle(2.4,2.4),DEPTH)
            cutters.extend((Pos(111-x0,cy-y0,SURFACE-DEPTH)*mark).solids())
    if cutters:s=s.cut(*cutters)
    assert len(s.solids())==1
    s.label=('southwest','southeast','northwest','northeast')[index]+'_panel'
    s.color=Color(.48,.57,.58)
    return s
