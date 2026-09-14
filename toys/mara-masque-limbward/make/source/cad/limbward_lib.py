"""Limbward component geometry, mm. Text-derived original design; no hardware."""
from build123d import *
from math import cos, sin, radians

# [specified] Wish dimensions; [assumed] detail parameters from reviewed handoff.
BODY_W, BODY_D, BODY_H = 196., 178., 22.
BODY_Y, CORNER, RIM_H = 9., 4., 4.
BOARD_W, BOARD_Y, PITCH = 160., 10., 20.
FOOT_R, FOOT_H, SCALLOP_R, SCALLOP_AT = 8., 4., 3., 9.
HEIGHTS = {'king':22., 'queen':28., 'rook':34., 'bishop':26., 'knight':24., 'pawn':12.}
COLORS = {'white': (0.93,0.89,0.77), 'black': (0.19,0.28,0.34), 'camera': (0.40,0.49,0.53)}
VANE_L, VANE_T, POST_R = 12., 3., 6.
GROOVE_OUT, GROOVE_IN, GROOVE_DEPTH = 18., 14., 0.6
LENS_W, LENS_H, LENS_BACK, LENS_FRONT, LENS_BEVEL = 68.,24.,-76.,-98.,4.
GRIP_X, GRIP_Y, GRIP_W, GRIP_D = 91.,6.,14.,144.


def prism_xy(points, height, z=0):
    return Pos(0,0,z) * extrude(Polygon(*points, align=None), amount=height)


def chamfered_rect(w,d,c):
    x,y=w/2,d/2
    return [(-x+c,-y),(x-c,-y),(x,-y+c),(x,y-c),(x-c,y),(-x+c,y),(-x,y-c),(-x,-y+c)]


def camera_board():
    body = Pos(0,BODY_Y,0) * prism_xy(chamfered_rect(BODY_W,BODY_D,CORNER),BODY_H)
    rim_outer = Pos(0,BOARD_Y,BODY_H) * extrude(Rectangle(176,176)-Rectangle(BOARD_W,BOARD_W), amount=RIM_H)
    body += rim_outer
    # Broad flat-bottomed octagonal lens is integral. Lower bevels are 45 degrees.
    profile=[(-30,0),(30,0),(34,4),(34,20),(30,24),(-30,24),(-34,20),(-34,4)]
    lens = Pos(0,LENS_BACK,0) * extrude(Plane.XZ * Polygon(*profile,align=None), amount=22)
    body += lens
    # Review r1 repair: a concentric surround and solid circular optical centre
    # replace the handle-like oval pocket; shallow 45-degree relief needs no hardware.
    outer=loft([Pos(0,-98.1,12)*(Plane.XZ*Ellipse(29.2,10.2)),
                Pos(0,-97,12)*(Plane.XZ*Ellipse(27,8))],ruled=True)
    centre=loft([Pos(0,-98.2,12)*(Plane.XZ*Circle(5.8)),
                 Pos(0,-96.9,12)*(Plane.XZ*Circle(7.8))],ruled=True)
    body -= outer-centre
    # Second circular optical ring, recessed into the solid centre.
    body -= loft([Pos(0,-98.1,12)*(Plane.XZ*Circle(3.2)),
                  Pos(0,-97.5,12)*(Plane.XZ*Circle(2))],ruled=True)
    # Asymmetric forward grip projects beside the barrel inside the same envelope.
    grip=Pos(89,-73,0)*prism_xy(chamfered_rect(18,50,4),24)
    body += grip
    body += Pos(GRIP_X,GRIP_Y,BODY_H)*extrude(Rectangle(GRIP_W,GRIP_D),amount=2)
    body += Pos(89,-86,23)*Cylinder(6,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
    for y in (-35,5,45):
        body -= Pos(92,y,22)*Box(10,2,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
    for rank in range(8):
        for file in range(8):
            if (rank+file)%2==0:
                groove=extrude(Rectangle(GROOVE_OUT,GROOVE_OUT)-Rectangle(GROOVE_IN,GROOVE_IN),amount=1.6)
                body -= Pos(-70+PITCH*file,-60+PITCH*rank,BODY_H-GROOVE_DEPTH)*groove
    body.label='camera_board'
    body.color=Color(*COLORS['camera'])
    assert len(body.solids())==1
    return body


def foot(side):
    shape=Cylinder(FOOT_R,FOOT_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    if side=='black':
        for deg in (0,120,240):
            shape -= Pos(SCALLOP_AT*cos(radians(deg)),SCALLOP_AT*sin(radians(deg)),-1)*Cylinder(SCALLOP_R,FOOT_H+2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return shape


def king_form():
    stem=Pos(0,0,3)*Cylinder(POST_R,13,align=(Align.CENTER,Align.CENTER,Align.MIN))
    dome=(Pos(0,0,16)*Sphere(POST_R)) & (Pos(0,0,16)*Box(20,20,10,align=(Align.CENTER,Align.CENTER,Align.MIN)))
    return stem+dome


def queen_form():
    stem=Pos(0,0,3)*Cylinder(POST_R,25,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return stem-Pos(0,0,18)*Cylinder(3,11,align=(Align.CENTER,Align.CENTER,Align.MIN))


def rook_form():
    a=Pos(0,0,3)*Box(VANE_L,VANE_T,31,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return a+Rot(0,0,90)*a


def bishop_form():
    # Truncated 45-degree crest, 3 mm plateau, distinguishes freely rotated bishop.
    p=Plane.XZ*Polygon((-6,3),(6,3),(6,21.5),(1.5,26),(-1.5,26),(-6,21.5),align=None)
    a=Pos(0,1.5,0)*extrude(p,amount=VANE_T)
    return Rot(0,0,45)*(a+Rot(0,0,90)*a)


def knight_form():
    a=Pos(0,0,3)*Box(12,8,9,align=(Align.CENTER,Align.CENTER,Align.MIN))
    a+=Pos(2,0,11)*Box(8,8,9,align=(Align.CENTER,Align.CENTER,Align.MIN))
    a+=Pos(4,0,19)*Box(4,8,5,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return a


def pawn_form():
    p=Plane.YZ*Polygon((-4,3),(4,3),(4,12),(-4,8),align=None)
    return Pos(-5,0,0)*extrude(p,amount=10)


BUILDERS={'king':king_form,'queen':queen_form,'rook':rook_form,'bishop':bishop_form,'knight':knight_form,'pawn':pawn_form}

def piece(side,role):
    result=foot(side)+BUILDERS[role]()
    result.label=side+'_'+role
    result.color=Color(*COLORS[side])
    assert len(result.solids())==1
    return result
