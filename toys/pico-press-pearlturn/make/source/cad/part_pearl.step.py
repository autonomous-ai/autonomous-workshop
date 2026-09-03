from build123d import Axis, Location, Vector
from pearlturn_lib import build_pearl

PRINTABLE = True

def gen_step():
    pearl = build_pearl().rotate(Axis.X, 90)
    bb = pearl.bounding_box()
    return Location(Vector(0, 0, -bb.min.Z)) * pearl
