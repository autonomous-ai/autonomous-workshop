"""Original text interpretation. All dimensions mm; X span, Y rear, Z up.
Lessons: generous journals, no flex hinges, positive return, resolved face marks.
"""
import math
from build123d import *
import cadfits

# Assumed manufacturing parameters; derived mating dimensions.
PIN_D = 8.0
BODY_PIN_D = 9.0
BODY_BORE_D = cadfits.slot_for(BODY_PIN_D,0.4)
BORE_D = cadfits.slot_for(PIN_D, 0.4)
KEY_T = 2.4
KEY_SLOT = cadfits.slot_for(KEY_T, 0.2)
PIVOT_Z = 58.0
DRIVE_H = 50.0
ANGLE = 18.0
GAP = 0.4
BASE_X, BASE_Y, BASE_T = 110.0, 70.0, 6.0
BEAM_HALF, BEAM_D, BEAM_H = 94.0, 10.0, 12.0
STAND_FRONT, STAND_BACK = 10.4, 20.4
BODY_FRONT, SKIN_BACK = -14.0, -10.0
SLIDE_FRONT, SLIDE_BACK = -9.6, -6.6
COVER_FRONT, COVER_BACK = -6.2, -3.2
SOCKET_X, SOCKET_Y = 16.8, 6.0
TONGUE_X = cadfits.peg_for(SOCKET_X, 'free')
TONGUE_Y = cadfits.peg_for(SOCKET_Y, 'free')
BODY_CENTRES = (-60.0, 60.0)
SLOT_W = BORE_D
SLOT_Z0, SLOT_Z1 = 46.7, 50.3
MASK_LEFT, MASK_RIGHT = -76.0, -41.0
TEAR_MASK_LEFT, TEAR_MASK_RIGHT = 41.0, 76.0
COLOURS = {'gray':(0.62,0.63,0.62),'cocoa_brown':(0.70,0.38,0.12),
           'dark_brown':(0.31,0.17,0.11),'misty_blue':(0.41,0.65,0.80),'black':(0.03,0.03,0.03),'beige':(0.85,0.69,0.46)}
ROLES = ['base','stand','beam','bull_body','bear_body','shuttle','bear_mask',
         'mouth_back','tear_back','main_pin','retainer','mount_pin','bear_face','bull_muzzle']
ROLE_COLOUR = dict(zip(ROLES,['gray','gray','gray','cocoa_brown','dark_brown',
                      'beige','dark_brown','dark_brown','misty_blue','gray','gray','gray','black','beige']))
assert 0.39 < (BORE_D-PIN_D)/2 < 0.41
assert SLOT_Z0 < DRIVE_H*math.cos(math.radians(ANGLE))-0.3
assert SLOT_Z1 >= DRIVE_H+0.3
assert SLIDE_FRONT-SKIN_BACK >= GAP-1e-9
assert COVER_FRONT-SLIDE_BACK >= GAP-1e-9

def prism(profile, y0, depth):
    return Pos(0,y0,0)*extrude(Plane.XZ*profile, amount=depth, dir=(0,1,0))

def rectangle(x0,x1,z0,z1,y0,depth):
    return prism(Pos((x0+x1)/2,(z0+z1)/2)*Rectangle(x1-x0,z1-z0),y0,depth)

def disc(x,z,r,y0,depth):
    return prism(Pos(x,z)*Circle(r),y0,depth)

def poly(points,y0,depth):
    return prism(Polygon(*points,align=None),y0,depth)

def through_bore(x,z,y0,depth):
    return disc(x,z,BORE_D/2,y0,depth)

def colour(part,role):
    part.label=role+'_'+ROLE_COLOUR[role]
    part.color=Color(*COLOURS[ROLE_COLOUR[role]])
    return part

def base():
    slab=extrude(RectangleRounded(BASE_X,BASE_Y,8),amount=BASE_T)
    boss=Pos(0,15.4,13)*Box(30,10,14)
    slot=Pos(0,16.6,13.2)*Box(SOCKET_X,cadfits.slot_for(7.6,0.4),14.4)
    return (slab+boss)-slot-through_bore(0,13,9.4,12)

def stand():
    mast=rectangle(-12,12,20,119,STAND_FRONT,10)
    tongue=rectangle(-TONGUE_X/2,TONGUE_X/2,6.4,20,12.8,7.6)
    stop_top=PIVOT_Z-33*math.tan(math.radians(ANGLE))-6/math.cos(math.radians(ANGLE))
    stop=rectangle(-33,33,34,stop_top,5,STAND_BACK-5)
    peg=disc(0,PIVOT_Z+DRIVE_H,PIN_D/2,-10,30.4)
    return (mast+tongue+stop+peg)-[through_bore(0,PIVOT_Z,9.4,12),through_bore(0,13,11.8,9.6)]

def beam():
    body=rectangle(-BEAM_HALF,BEAM_HALF,-6,6,0,BEAM_D)+disc(0,0,11,0,BEAM_D)
    cuts=[through_bore(0,0,-1,12)]
    for x in BODY_CENTRES:
        cuts.append(disc(x,0,BODY_BORE_D/2,-1,12))
    return body-cuts

def animal_outline(is_bull):
    c=-60 if is_bull else 60
    body=rectangle(c-38,c+38,27,55,BODY_FRONT,14)
    head=prism(Pos(c,47)*Ellipse(37,17),BODY_FRONT,14)
    torso=poly([(c-34,27),(c-26,13),(c+26,13),(c+34,27)],BODY_FRONT,14)
    feet=[rectangle(c+d-7,c+d+7,6,10.4,BODY_FRONT,24).fuse(rectangle(c+d-7,c+d+7,6,23,BODY_FRONT,4)) for d in [-21,21]]
    bridge=rectangle(c-27,c+27,6,10.4,BODY_FRONT,24)
    tongue=disc(c,0,8,BODY_FRONT,4).fuse(disc(c,0,BODY_PIN_D/2,SKIN_BACK,25.2))
    extras=[]
    if is_bull:
        left=[(-72,54),(-84,54),(-94,59),(-101,67),(-102,73),(-98.4,74),(-96,68),(-91,64),(-83,61),(-72,61)]
        right=[(-98-x,z) for x,z in reversed(left)]
        extras=[poly(left,BODY_FRONT,4),poly(right,BODY_FRONT,4)]
    else:
        extras=[disc(c+d,62,7,BODY_FRONT,14) for d in [-25,25]]
    body=body.fuse(head,torso,bridge,tongue,*feet,*extras)
    # Open cavity prints without a roof. Rear cover is retained on two integral
    # printed pins rather than an undercut slide channel (print-gate repair).
    lower=rectangle(c-35,c+35,10.4,27,SKIN_BACK,11)
    upper=rectangle(c-35,c+35,26.9,52 if is_bull else 70,SKIN_BACK,11)
    track=rectangle(c-41,c+41,16.6,23.4,SKIN_BACK,3.8)
    body=body-[lower,upper,track]
    if not is_bull:
        body=body-rectangle(38.6,59.4,51.9,70,SKIN_BACK,11)
        body=body-rectangle(38.6,59.4,44.4,70,-12.8,2.8)
    inner=rectangle(-25.4,-20,23,58.4,SKIN_BACK,11) if is_bull else rectangle(20,25.4,23,58.4,SKIN_BACK,11)
    body=body-inner
    for dx in ([-27,27] if is_bull else [-25,25]):
        pin_z=55 if is_bull else 62
        half=4 if is_bull else 3.2
        body=body.fuse(rectangle(c+dx-half,c+dx+half,pin_z-half,pin_z+half,SKIN_BACK,18))
        body=body-rectangle(c+dx-KEY_SLOT/2,c+dx+KEY_SLOT/2,pin_z-6,pin_z+6,3.8,KEY_SLOT)
    body=body-rectangle(c-KEY_SLOT/2,c+KEY_SLOT/2,-6,6,10.4,KEY_SLOT)
    if is_bull:
        body=body-muzzle_plug(0.4,seat=True)
        eyes=[(-62,49),(-36,49)]
        cuts=[disc(x,z,2,-14.1,5.4) for x,z in eyes]
        brow=[(-68,54),(-57,51),(-57,52.8),(-68,55.8)]
        ear=[(-94,50),(-88,47.5),(-79,49),(-74,52),(-81,54),(-89,53.5)]
        cheek=[(-72.8,53),(-71.2,53),(-67.2,42),(-68.8,42)]
        for profile in [brow,ear,cheek]:
            cuts.extend([poly(profile,-14.1,1.3),poly([(-98-x,z) for x,z in reversed(profile)],-14.1,1.3)])
        for x in [-81,-39]:
            cuts.append(rectangle(x-.8,x+.8,7,17,-14.1,1.3))
    else:
        body=body-[prism(tear_profile(x),-15,6) for x in [44,54]]
        cuts=[disc(x,56.7,2,-14.1,5.4) for x in [44,54]]
        cuts += [prism(Pos(49,52)*Ellipse(3,1.6),-14.1,5.4),rectangle(46,52,33,34.2,-14.1,1.4)]
        cuts += [disc(c+d,62,3.5,-14.1,1.4) for d in [-25,25]]
    return body-cuts

def tear_profile(x):
    return Polygon((x-.8,54.9),(x+.8,54.9),(x+.8,52.3),(x+1.7,50.8),(x+2.1,49.2),(x-2.1,49.2),(x-1.7,50.8),(x-.8,52.3),align=None).fuse(Pos(x,49.2)*Circle(2.1))

def muzzle_plug(clearance=0,seat=False):
    front=Pos(-49,39)*Ellipse(17+clearance,11+clearance)
    back=Pos(-49,39)*Ellipse(18+clearance,12+clearance)
    taper=loft([Pos(0,-13.2,0)*(Plane.XZ*front),Pos(0,-11.6,0)*(Plane.XZ*back)])
    return prism(front,-14.1 if seat else -14,.9 if seat else .8).fuse(taper,prism(back,-11.6,1.7 if seat else 1.2))

def bull_muzzle():
    plug=muzzle_plug()
    pads=[rectangle(x,x+3,43,46,-10.4,3.8) for x in [-64,-37]]
    smile=Polygon((-56,36.5),(-42,36.5),(-43,32),(-46,30),(-52,30),(-55,32),align=None)
    cuts=[prism(smile,-15,9),rectangle(-57,-41,40.5,41.7,-15,9),disc(-56,44.2,1.5,-15,9),disc(-46,44.2,1.5,-15,9)]
    return plug.fuse(*pads)-cuts

def bull_body(): return animal_outline(True)
def bear_body(): return animal_outline(False)

def shuttle():
    bar=rectangle(-78,78,17,23,SLIDE_FRONT,3)
    left=rectangle(MASK_LEFT,MASK_RIGHT,28,39.5,SLIDE_FRONT,3)
    neck=rectangle(-74,-69,20,31,SLIDE_FRONT,3)
    tower=rectangle(-8,8,20,58,SLIDE_FRONT,3)
    right=rectangle(58,63,20,30,SLIDE_FRONT,3).fuse(rectangle(56,65,29,32,SLIDE_FRONT,3))
    # Bear-mask locating tongue rises into an open-bottom pocket.
    slot=prism(Pos(0,(SLOT_Z0+SLOT_Z1)/2)*SlotOverall(SLOT_Z1-SLOT_Z0+SLOT_W,SLOT_W,rotation=90),SLIDE_FRONT-1,5)
    return bar.fuse(left,neck,tower,right)-slot

def bear_mask():
    mask=rectangle(TEAR_MASK_LEFT,TEAR_MASK_RIGHT,26,55.5,SLIDE_FRONT,3)
    pocket=rectangle(57.6,63.4,25,29.6,SLIDE_FRONT-1,5).fuse(rectangle(55.6,65.4,28.6,32.4,SLIDE_FRONT-1,5))
    return mask-pocket

def cover(is_bull):
    c=-60 if is_bull else 60
    # Rear face is planar for bed placement; front pad is the fixed colour backing
    # and the axial guide behind the common shuttle. Captured by two cross-keys.
    panel=rectangle(c-34.6,c+34.6,27.4,51.6,COVER_FRONT,9.6)
    stem=rectangle(c-22,c+22,10.8,28,COVER_FRONT,9.6)
    if is_bull:
        rail=rectangle(c-34.6,c+34.6,50,62,0.4,3)
        holes=[rectangle(c+d-4.4,c+d+4.4,50.6,59.4,COVER_FRONT-1,12) for d in [-27,27]]
    else:
        rail=rectangle(35,85,57.2,60.2,0.4,3)
        rail=rail.fuse(*[disc(x,62,6.4,0.4,3) for x in [35,85]])
        panel=panel.fuse(rectangle(39,59,51.5,55.3,COVER_FRONT,9.6),rectangle(44,54,54,62.2,COVER_FRONT,9.6))
        holes=[rectangle(x-3.6,x+3.6,58.4,65.6,COVER_FRONT-1,12) for x in [35,85]]
    return (panel+stem+rail)-holes

def mouth_back(): return cover(True)
def tear_back():
    return cover(False)-rectangle(45,53,56.8,62.3,COVER_FRONT-0.1,3.1)

def bear_face():
    plate=rectangle(39,59,44.8,61.8,-12.4,2)
    plate=plate-[prism(offset(tear_profile(x),amount=.3),-13,4) for x in [44,54]]
    key=rectangle(45.5,52.5,57.2,61.8,-10.4,6.8)
    return plate+key

def pin(main):
    stack=20.4 if main else 10.0
    shaft_end=stack+5.2
    shaft=disc(0,0,PIN_D/2,-0.4,shaft_end+0.4)
    head=disc(0,0,6,-3,2.6)
    cross=rectangle(-KEY_SLOT/2,KEY_SLOT/2,-6,6,stack+0.4,KEY_SLOT)
    return (shaft+head)-cross

def main_pin(): return pin(True)
def mount_pin(): return pin(False)

def retainer():
    stem=rectangle(-KEY_T/2,KEY_T/2,-6,4.4,0,KEY_T)
    head=rectangle(-3.5,3.5,4.4,6.8,0,KEY_T)
    return stem+head

BUILDERS={r:globals()[r] for r in ROLES}

def print_part(role):
    part=BUILDERS[role]()
    if role=='base':
        pass
    elif role in ['main_pin','mount_pin']:
        # Shaft builds vertically from its broad head; cross-slot bridge only 2.8mm.
        part=Rot(90,0,0)*part
    elif role in ['stand','mouth_back','tear_back']:
        part=Rot(-90,0,0)*part
    else:
        part=Rot(90,0,0)*part
    bb=part.bounding_box()
    part=Pos(-(bb.min.X+bb.max.X)/2,-(bb.min.Y+bb.max.Y)/2,-bb.min.Z)*part
    assert len(part.solids())==1, (role,len(part.solids()))
    return colour(part,role)
