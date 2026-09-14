"""Moon Fan: mm, XY silhouette, +Z front. Coil dimensions precede shape."""
from build123d import *
from math import sin, cos, radians
INLAY_X, INLAY_Y, INLAY_Z = 11.5, 21.5, 0.75
POCKET_X, POCKET_Y, POCKET_D = 12.5, 22.5, 1.05
COIL_X, COIL_Y, WINDOW = -28.5, 0.0, 1.0
KEEP_X, KEEP_Y, KEEP_Z = 15.5, 25.5, 3.25
PIVOT = (-10.0,29.0)
SWING, BODY_H, LEAF_Z, LEAF_H = 75.0,4.6,5.0,2.4
PIN_R, BORE_R = 2.2,2.4
PEG_R, PEG_ORBIT = 1.5,8.0

def box(x,y,z,px=0,py=0,pz=0):
    return Pos(px,py,pz)*Box(x,y,z,align=(Align.CENTER,Align.CENTER,Align.MIN))

def cyl(r,h,x=0,y=0,z=0):
    return Pos(x,y,z)*Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))

def named(s,label,rgb):
    s.label=label
    s.color=Color(*rgb)
    return s

def silhouette(h,z=0):
    # Truncate analytic cusps; round terminal corners in the 2-D outline.
    face=Circle(43)-Pos(17,0)*Circle(33)
    face=face & Pos(-13,0)*Rectangle(74,100)
    face=fillet(face.vertices(),radius=0.8)
    return Pos(0,0,z)*extrude(face,h)

def inlay_datum():
    return box(INLAY_X,INLAY_Y,INLAY_Z,COIL_X,0,WINDOW)

def pocket():
    return box(POCKET_X,POCKET_Y,POCKET_D,COIL_X,0,WINDOW)

def keepout():
    return box(KEEP_X,KEEP_Y,KEEP_Z,COIL_X)

def window_wall():
    return box(KEEP_X,KEEP_Y,WINDOW,COIL_X)

def orbit(a):
    return (PIVOT[0]+PEG_ORBIT*cos(radians(180+a)),PIVOT[1]+PEG_ORBIT*sin(radians(180+a)))

def track_tool():
    # Annular-sector channel with tangent stop planes exactly one peg radius
    # beyond each endpoint. Wider radial walls supply 0.4 mm running clearance.
    a0,a1=180,180+SWING
    e1=CenterArc(PIVOT,9.9,a0,SWING)
    e2=Line(e1@1,(PIVOT[0]+6.1*cos(radians(a1)),PIVOT[1]+6.1*sin(radians(a1))))
    e3=CenterArc(PIVOT,6.1,a1,-SWING)
    e4=Line(e3@1,e1@0)
    s=Pos(0,0,3.0)*extrude(Face(Wire([e1,e2,e3,e4])),3.0,dir=(0,0,1))
    for a in (0,SWING):
        x,y=orbit(a)
        s=s+cyl(1.9,3,x,y,3)
    # Start tangent points down, end tangent points down/right.
    for a,sign in ((0,1),(SWING,-1)):
        x,y=orbit(a)
        theta=radians(180+a)
        tx,ty=-sin(theta)*sign,cos(theta)*sign
        clip=Pos(x+tx*(50-PEG_R),y+ty*(50-PEG_R),3)*Rot(0,0,180+a+90+(180 if sign<0 else 0))*Box(100,100,3,align=(Align.CENTER,Align.CENTER,Align.MIN))
        s=s & clip
    return s

def carrier():
    s=silhouette(BODY_H)
    # Flat pocket, then larger service recess. Enclosure sidewalls are explicit.
    s=s-box(POCKET_X,POCKET_Y,6,COIL_X,0,WINDOW)
    s=s-box(18.3,28.3,5,COIL_X,0,2.05)
    # Cover tongue wells and thin capture roofs beyond the keep-out.
    for sign in (-1,1):
        s=s-box(8.8,4.2,5,COIL_X,sign*15.7,2.05)
        s=s+box(8.8,1.2,1.05,COIL_X,sign*17.55,3.55)
    s=s-cyl(BORE_R,8,*PIVOT,-1)
    s=s-track_tool()
    # Side purchase recess for thumbnail, also shows which lid lifts.
    s=s-box(3,6,4,-38,0,2.05)
    # Recessed tactile frame: full flat landing remains at Z0.
    outer=loft([Pos(COIL_X,0,0)*Rectangle(17.5,27.5),Pos(COIL_X,0,0.8)*Rectangle(16.5,26.5)],ruled=True)
    inner=loft([Pos(COIL_X,0,-0.1)*Rectangle(15.375,25.375),Pos(COIL_X,0,0.8)*Rectangle(16.5,26.5)],ruled=True)
    landmark=outer-inner
    s=s-landmark
    return named(s,'carrier',(0.16,0.23,0.33))

def leaf():
    s=silhouette(LEAF_H,LEAF_Z)
    x,y=orbit(0)
    s=s+cyl(PEG_R,1.8,x,y,3.2)
    s=s-cyl(BORE_R,8,*PIVOT,1)
    # Both broad terminal side faces are tangible opposing press surfaces.
    return named(s,'leaf',(1.0,0.71,0.29))

def cover():
    s=box(17.5,27.5,1.2,COIL_X,0,2.05)
    for sign in (-1,1):
        # Flat resilient tongue; nose fits under the integral capture roof.
        s=s+box(8,3.2,1.2,COIL_X,sign*15.2,2.05)
        s=s+box(8,0.5,1.2,COIL_X,sign*16.95,2.05)
    return named(s,'cover',(0.31,0.62,0.68))

def pin():
    # Printed head on bed; assembly translates down 1.6 mm.
    shaft=cyl(PIN_R,7.6,0,0,1.6)
    shaft=shaft+Pos(0,0,9.2)*Cone(2.2,2.7,0.8,align=(Align.CENTER,Align.CENTER,Align.MIN))
    shaft=shaft+cyl(2.7,0.8,0,0,10.0)
    shaft=shaft+Pos(0,0,10.8)*Cone(2.7,2.2,0.5,align=(Align.CENTER,Align.CENTER,Align.MIN))
    shaft=shaft & box(8,3.2,12)
    s=cyl(4,1.6)+shaft
    s=s-box(1.0,8,8,0,0,4.4)
    return named(s,'pin',(0.31,0.62,0.68))
