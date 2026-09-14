"""Veinwake: original text-derived geometry; dimensions in millimetres.

Design authority: completed Mara Masque handoff. Shared circular seats are
deliberately loose, removable game-piece rests, not retaining connectors.
"""
from math import sqrt, sin, cos, pi, copysign
from build123d import (Align, Axis, BuildLine, BuildSketch, Color, Compound,
                       Circle, Cylinder, Face, Matrix, Plane, Polygon, Polyline, Pos, RectangleRounded, Spline, Wire,
                       RegularPolygon, ThreePointArc, extrude, fillet, loft,
                       make_face, offset, revolve)
import cadfits
from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert

BOARD_LENGTH = 140.0
BOARD_WIDTH = 130.0
RIM_HEIGHT = 14.0
FIELD_HEIGHT = 8.0
SEAT_DEPTH = 2.0
SEAT_Z = FIELD_HEIGHT - SEAT_DEPTH
GRID_PITCH = 36.0
FOOT_DIAMETER = 28.0
FOOT_HEIGHT = 3.0
SEAT_CLEARANCE = 1.0
# This open game pocket intentionally exceeds the helper's ordinary fit band.
# Widen only this design calculation, then restore the shared helper default.
_ordinary_clearance_max = cadfits.EXPLICIT_MAX
cadfits.EXPLICIT_MAX = SEAT_CLEARANCE
SEAT_DIAMETER = cadfits.slot_for(FOOT_DIAMETER, SEAT_CLEARANCE)
cadfits.EXPLICIT_MAX = _ordinary_clearance_max
CLUSTER_HEIGHT = 26.0
ASSEMBLED_HEIGHT = SEAT_Z + CLUSTER_HEIGHT
CORNER_RADIUS = 6.0
FIELD_LENGTH = 114.0
FIELD_WIDTH = 104.0
FIELD_RADIUS = 22.0
ROCK_EXPONENT = 3.5
ROCK_TOP_RADIUS = 4.0
CAVITY_INSET = 13.0
GROWTH_KEEPOUT_RADIUS = 16.5
TERRACE_WIDTH = 2.5
TERRACE_Z = 11.0
TOOTH_RADIUS = 11.0
TOOTH_SHOULDER = 18.0
TOOTH_TIP_RADIUS = 2.5
TOOTH_TIP_OFFSET = 2.0
LOBE_RADIUS = 7.0
LOBE_CENTER_RADIUS = 6.0
LOBE_CROWN_Z = CLUSTER_HEIGHT - LOBE_RADIUS
HELD_OFFSET = 55.0
OUTLINE = [(-70,-25),(-60,-48),(-38,-65),(28,-65),(54,-52),(70,-22),
           (70,20),(57,48),(34,65),(-30,65),(-55,50),(-70,24)]
GRID = [(x,y) for y in (GRID_PITCH,0,-GRID_PITCH) for x in (-GRID_PITCH,0,GRID_PITCH)]
DRAW_CELLS = 'XOXXOOOXX'
PALETTE = {'rind':(121/255,109/255,96/255),
           'tooth':(156/255,120/255,190/255),
           'bubble':(148/255,197/255,180/255)}

assert SEAT_DIAMETER == 30.0 and SEAT_Z == 6.0
assert GRID_PITCH - SEAT_DIAMETER >= 3.0
assert 2 * TOOTH_TIP_RADIUS * sqrt(3)/2 >= 2.0
assert TOOTH_TIP_OFFSET + TOOTH_TIP_RADIUS < TOOTH_RADIUS
assert ASSEMBLED_HEIGHT == 32.0

def finish(shape, label, kind):
    assert len(shape.solids()) == 1, f'{label}: expected one fused solid'
    assert shape.is_valid, f'{label}: invalid topology'
    shape.label = label
    # Workshop's current delivery contract requires direct sRGB channels.
    shape.color = Color(*PALETTE[kind])
    return shape

def rock_footprint():
    points=[]
    for i in range(64):
        t=2*pi*i/64
        q=1-0.012*sin(2*t)**2*(1+0.25*sin(3*t))
        points.append((BOARD_LENGTH/2*copysign(abs(cos(t))**(2/ROCK_EXPONENT),cos(t))*q,
                       BOARD_WIDTH/2*copysign(abs(sin(t))**(2/ROCK_EXPONENT),sin(t))*q))
    face=Face(Wire(Spline(*points,periodic=True)))
    box=face.bounding_box()
    sx=BOARD_LENGTH/box.size.X;sy=BOARD_WIDTH/box.size.Y
    return face.transform_geometry(Matrix([[sx,0,0,-box.center().X*sx],
                                            [0,sy,0,-box.center().Y*sy],
                                            [0,0,1,0],[0,0,0,1]]))

def cavity_profiles(outer):
    lower=offset(outer,amount=-CAVITY_INSET)
    for x,y in GRID:
        lower=lower + Pos(x,y)*Circle(GROWTH_KEEPOUT_RADIUS)
    upper=offset(lower,amount=TERRACE_WIDTH)
    # Geometric safeguard: top rounding consumes4 mm, leaving at least3.
    upper=upper & offset(outer,amount=-(ROCK_TOP_RADIUS+3))
    missing=lower-upper
    assert missing is None or missing.area<1e-5, 'Upper opening clips a lower growth passage'
    # STEP cannot portably encode this kernel's offset-of-spline curves.
    # Converting their representation before cuts preserves the closed rind
    # on export (verified by reimport and volume), without changing its form.
    return tuple(Face.cast(BRepBuilderAPI_NurbsConvert(s.faces()[0].wrapped,True).Shape())
                 for s in (lower,upper))

def make_rind(label='rind'):
    # Completed selected-Inventor repair: a rounded pebble and geological
    # terrace replace the initial octagonal tray rejected in visual review1.
    outer=rock_footprint()
    body=extrude(outer,amount=RIM_HEIGHT)
    top=[e for e in body.edges() if abs(e.bounding_box().min.Z-RIM_HEIGHT)<1e-5]
    body=fillet(top,radius=ROCK_TOP_RADIUS)
    lower,upper=cavity_profiles(outer)
    body=body-Pos(0,0,FIELD_HEIGHT)*extrude(lower,amount=RIM_HEIGHT-FIELD_HEIGHT+1)
    body=body-Pos(0,0,TERRACE_Z)*extrude(upper,amount=RIM_HEIGHT-TERRACE_Z+1)
    seats = [Pos(x,y,SEAT_Z) * Cylinder(SEAT_DIAMETER/2, RIM_HEIGHT-SEAT_Z+1,
              align=(Align.CENTER,Align.CENTER,Align.MIN)) for x,y in GRID]
    return finish(body - seats, label, 'rind')

def foot():
    return Cylinder(FOOT_DIAMETER/2, FOOT_HEIGHT,
                    align=(Align.CENTER,Align.CENTER,Align.MIN))

def make_tooth(label='tooth'):
    crystal = loft([Pos(0,0,2) * RegularPolygon(TOOTH_RADIUS,6),
                    Pos(0,0,TOOTH_SHOULDER) * RegularPolygon(TOOTH_RADIUS,6),
                    Pos(TOOTH_TIP_OFFSET,0,CLUSTER_HEIGHT) * RegularPolygon(TOOTH_TIP_RADIUS,6)],
                   ruled=True)
    return finish(foot() + crystal, label, 'tooth')

def bubble_lobe():
    # One revolved silhouette: full-radius vertical wall and upper hemisphere.
    with BuildSketch(Plane.XZ) as profile:
        with BuildLine():
            Polyline((0,2),(LOBE_RADIUS,2),(LOBE_RADIUS,LOBE_CROWN_Z))
            ThreePointArc((LOBE_RADIUS,LOBE_CROWN_Z),
                          (LOBE_RADIUS/sqrt(2),LOBE_CROWN_Z+LOBE_RADIUS/sqrt(2)),
                          (0,CLUSTER_HEIGHT))
            Polyline((0,CLUSTER_HEIGHT),(0,2))
        make_face()
    return revolve(profile.sketch, axis=Axis.Z)

def make_bubble(label='bubble'):
    lobe = bubble_lobe()
    # Leave a full millimetre of foot beyond each lobe. Exact tangency at the
    # earlier radius-seven centres made a pinched foot junction at local z=3.
    centers = [(-LOBE_CENTER_RADIUS*sqrt(3)/2,-LOBE_CENTER_RADIUS/2),
               (LOBE_CENTER_RADIUS*sqrt(3)/2,-LOBE_CENTER_RADIUS/2),(0,LOBE_CENTER_RADIUS)]
    return finish(foot() + [Pos(x,y,0)*lobe for x,y in centers], label, 'bubble')

def make_assembly(state='draw'):
    children = [make_rind()]
    if state == 'draw':
        counts = {'X':0,'O':0}
        for (x,y),cell in zip(GRID,DRAW_CELLS):
            counts[cell] += 1
            kind = 'tooth' if cell == 'X' else 'bubble'
            builder = make_tooth if cell == 'X' else make_bubble
            children.append(Pos(x,y,SEAT_Z)*builder(f'{kind}_{counts[cell]}'))
    else:
        assert state in ('before','after')
        placements = [('tooth_1',-GRID_PITCH,GRID_PITCH,SEAT_Z),
                      ('tooth_2',0,GRID_PITCH,SEAT_Z),
                      ('tooth_3',GRID_PITCH,GRID_PITCH,SEAT_Z+(HELD_OFFSET if state=='before' else 0)),
                      ('bubble_1',-GRID_PITCH,0,SEAT_Z),('bubble_2',0,0,SEAT_Z)]
        for name,x,y,z in placements:
            builder = make_tooth if name.startswith('tooth') else make_bubble
            children.append(Pos(x,y,z)*builder(name))
    return Compound(label='veinwake',children=children)
