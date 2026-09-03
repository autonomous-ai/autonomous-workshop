from build123d import Axis, Location, Vector
from pearlturn_lib import build_shell

PRINTABLE = True

def gen_step():
    # Broad side face is placed on Z=0 for support-free printing.
    shell = build_shell().rotate(Axis.X, 90)
    bb = shell.bounding_box()
    return Location(Vector(0, 0, -bb.min.Z)) * shell
