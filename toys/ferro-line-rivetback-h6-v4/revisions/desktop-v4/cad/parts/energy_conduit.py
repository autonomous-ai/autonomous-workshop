from build123d import Circle, Polygon, extrude, make_face
from features.forms import color_part
from params import cable_rgb


def build():
    # Radial wedge boundaries keep the two cable ends square instead of
    # creating the knife edges produced by a rectangular ring clip.
    ring = make_face(Circle(16.0)) - make_face(Circle(13.5))
    wedge = make_face(Polygon((0.0, 0.0), (32.0, -48.0), (64.0, 0.0), (32.0, 48.0)))
    crescent = extrude(ring & wedge, amount=3.0)
    return color_part(
        crescent,
        "energy_conduit",
        cable_rgb,
    )
