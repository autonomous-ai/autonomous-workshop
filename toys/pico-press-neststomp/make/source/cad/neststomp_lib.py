"""Parametric geometry for the two-part Neststomp desk toy."""
from build123d import Axis, Box, Circle, Compound, Polygon, Pos, extrude, make_face

DEPTH = 24.0
OWL_W = 68.0
OWL_H = 80.0
BELLY_W = 54.0
BELLY_H = 34.0
CHICK_W = 36.0
CHICK_H = 33.0
CHICK_DEPTH = 22.4
DEPTH_GAP = (DEPTH - CHICK_DEPTH) / 2.0
END_CLEARANCE = 0.8
LEFT_X = -(BELLY_W - CHICK_W) / 2.0 + END_CLEARANCE
RIGHT_X = -LEFT_X

def _extruded_polygon(points, depth=DEPTH):
    face = make_face(Polygon(*points))
    return extrude(face, amount=depth)

def make_owl():
    # Friendly owl silhouette in XY, with broad flat rear face at Z=0.
    body_pts = [(-34,8),(-31,57),(-25,72),(-20,80),(-15,80),(-10,71),
                (0,76),(10,71),(15,80),(20,80),(25,72),(31,57),(34,8),
                (28,0),(15,0),(10,5),(-10,5),(-15,0),(-28,0)]
    owl = _extruded_polygon(body_pts)
    # Open tabletop corridor: 7 mm side walls act as broad stop faces.
    window = Box(BELLY_W, BELLY_H + 1, DEPTH + 2).moved(Pos(0, (BELLY_H-1)/2, DEPTH/2))
    owl = owl - window
    # Shallow recessed face marks preserve the exact 24 mm envelope and flat back.
    eye_l = extrude(make_face(Circle(6.5).moved(Pos(-11,58))), amount=0.8).moved(Pos(0,0,DEPTH-0.8))
    eye_r = extrude(make_face(Circle(6.5).moved(Pos(11,58))), amount=0.8).moved(Pos(0,0,DEPTH-0.8))
    pupil_l = extrude(make_face(Circle(2.4).moved(Pos(-11,58))), amount=1.0).moved(Pos(0,0,DEPTH-1.0))
    pupil_r = extrude(make_face(Circle(2.4).moved(Pos(11,58))), amount=1.0).moved(Pos(0,0,DEPTH-1.0))
    beak = _extruded_polygon([(-4,50),(4,50),(0,44)], 0.8).moved(Pos(0,0,DEPTH-0.8))
    owl = owl - eye_l - eye_r - pupil_l - pupil_r - beak
    owl.label = "owl_body_bridge_and_feet"
    assert len(owl.solids()) == 1
    return owl

def make_chick():
    # Rounded triangular cam: high central lobe and two stable low endpoint arcs.
    pts = [(-18,5),(-17,11),(-14,20),(-9,28),(-3,32),(0,33),
           (3,32),(9,28),(14,20),(17,11),(18,5),(16,2),(12,0),
           (-12,0),(-16,2)]
    chick = _extruded_polygon(pts, CHICK_DEPTH)
    # Friendly recessed face marks stay inside the 22.4 mm running depth.
    eye_l = extrude(make_face(Circle(2.0).moved(Pos(-6,19))), amount=0.7).moved(Pos(0,0,CHICK_DEPTH-0.7))
    eye_r = extrude(make_face(Circle(2.0).moved(Pos(6,19))), amount=0.7).moved(Pos(0,0,CHICK_DEPTH-0.7))
    beak = _extruded_polygon([(-3,13),(3,13),(0,9)], 0.7).moved(Pos(0,0,CHICK_DEPTH-0.7))
    chick = chick - eye_l - eye_r - beak
    chick.label = "chick_roller_cam"
    assert len(chick.solids()) == 1
    return chick

def make_assembly(chick_x=LEFT_X, owl_tilt_deg=0.0, chick_roll_deg=0.0,
                  ground_tilt=False):
    owl = make_owl().rotate(Axis.Z, owl_tilt_deg)
    # State renders keep the active foot on a shared tabletop datum.  This is
    # an exact rigid transform, not a deformation or an exploded view.
    if ground_tilt:
        owl = owl.moved(Pos(0, -owl.bounding_box().min.Y, 0))
    chick = (make_chick().rotate(Axis.Z, chick_roll_deg)
             .moved(Pos(chick_x, 0.0, DEPTH_GAP)))
    owl.label = "owl"
    chick.label = "nested_chick_cam"
    assembly = Compound(children=[owl, chick], label="neststomp")
    return assembly
