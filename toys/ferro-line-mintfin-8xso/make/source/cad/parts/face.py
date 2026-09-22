"""Cream expression plates and reusable colored facial landmarks.

Parts are authored in face coordinates (X=u, Y=v, Z=outward normal).
Plate back is Z=0 in assembly. The one-piece cream plate flips its expression
front to bed Z=0 and prints its blind magnet pockets facing up. Expression inserts use broad flat adhesive seats.
"""
from build123d import *
from params.face import *


def painted(shape, role, color):
    shape.label = role
    h=COLORS[color].lstrip('#')
    shape.color=Color(*(int(h[i:i+2],16)/255 for i in (0,2,4)))
    assert len(shape.solids()) == 1, (role,len(shape.solids()))
    return shape


def outline_face(scale=1.0):
    edge=Spline(*[(u*scale,v*scale) for u,v in OUTLINE],periodic=True)
    return Face(Wire([edge]))


def face_to_world(shape):
    return shape.rotate(Axis.X, FACE_ANGLE).translate(FACE_ORIGIN)


def plate():
    """One cream plate; back is n=0, three blind pockets open toward -n."""
    shape=extrude(outline_face(),amount=FACE_T,dir=(0,0,1))
    for u,v in MAGNETS:
        cutter=Pos(u,v,-.1)*Cylinder(MAGNET_D/2,MAGNET_DEPTH+.1,
                                    align=(Align.CENTER,Align.CENTER,Align.MIN))
        shape=shape-cutter
    return painted(shape,'cream_interchangeable_face_plate','cream')


def plate_print():
    """Solid expression front down; back magnet pockets face up."""
    shape=plate().rotate(Axis.X,180).translate((0,0,FACE_T))
    return painted(shape,'face_plate_print_front_down_pockets_up','cream')


def dome(radius,height):
    sphere_radius=(radius*radius+height*height)/(2*height)
    s=Pos(0,0,height-sphere_radius)*Sphere(sphere_radius)
    return s & Box(2*radius+2,2*radius+2,height,align=(Align.CENTER,Align.CENTER,Align.MIN))


def eye():
    shape=Cylinder(EYE_DIAMETER/2,EYE_FOOT_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    shape=shape.fuse(Pos(0,0,EYE_FOOT_HEIGHT)*dome(EYE_DIAMETER/2,EYE_HEIGHT-EYE_FOOT_HEIGHT))
    # Flat-bottom matching recess for the white highlight; no floating insert.
    shape=shape-Pos(-2,2.5,HIGHLIGHT_RECESS_FLOOR)*Cylinder(1.4,5,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return painted(shape,'happy_eye_with_highlight_seat','charcoal')


def highlight():
    return painted(Cylinder(1.4,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN)), 'white_eye_highlight','white')


def nostril():
    return painted(Cylinder(.8,NOSTRIL_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN)), 'nostril','charcoal')


def happy_mouth():
    # Rounded broad smile silhouette, with a coral tongue recess.
    f=Face(Wire([Spline((-8,3),(-5,4),(0,3),(5,4),(8,3),(6,-2),(3,-4.5),(0,-5),(-3,-4.5),(-6,-2),periodic=True)]))
    s=extrude(f,amount=2.0,dir=(0,0,1))
    s=s-Pos(0,TONGUE_CENTER_V,1.2)*extrude(Ellipse(4.5,2.75),amount=2)
    return painted(s,'happy_smile','charcoal')


def tongue():
    return painted(extrude(Ellipse(4.5,2.75),amount=TONGUE_HEIGHT),'happy_coral_tongue','coral')


def sleepy_lid():
    # A single curved closed ribbon, 1.2 mm wide, 1.2 mm standing height.
    outer=Spline((-7,1),(-3,-1.3),(0,-1.8),(3,-1.3),(7,1))
    inner=Spline((7,2.3),(3,0),(0,-.5),(-3,0),(-7,2.3))
    wire=Wire([outer,Line((7,1),(7,2.3)),inner,Line((-7,2.3),(-7,1))])
    shape=extrude(Face(wire),amount=1.2)
    shape=fillet(shape.edges().filter_by(Axis.Z),radius=.4)
    return painted(shape,'sleepy_closed_lid','charcoal')


def sleepy_mouth():
    return painted(extrude(Ellipse(2.4,1.6),amount=1.2),'sleepy_small_mouth','charcoal')


def face_instances(expression='happy'):
    """Return role, builder, face-local translation, color; no assembly made."""
    rows=[('face_plate',plate,(0,0,0),'cream')]
    rows += [(f'nostril_{side}',nostril,(side*3.5,-2,FACE_T),'charcoal') for side in (-1,1)]
    if expression=='happy':
        for side in (-1,1):
            rows += [(f'eye_{side}',eye,(side*14,3,FACE_T),'charcoal'),(f'highlight_{side}',highlight,(side*14-2,5.5,FACE_T+HIGHLIGHT_RECESS_FLOOR),'white')]
        rows += [('happy_mouth',happy_mouth,(0,-9,FACE_T),'charcoal'),('tongue',tongue,(0,-9+TONGUE_CENTER_V,FACE_T+1.2),'coral')]
    else:
        rows += [(f'lid_{side}',sleepy_lid,(side*14,3,FACE_T),'charcoal') for side in (-1,1)]
        rows += [('sleepy_mouth',sleepy_mouth,(0,-9,FACE_T),'charcoal')]
    return rows
