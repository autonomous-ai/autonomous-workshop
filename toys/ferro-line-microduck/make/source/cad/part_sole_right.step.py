from build123d import Axis
from duck_lib import build_boot

def gen_step():
    # Put the continuous front face on the bed; assembly geometry is unchanged.
    part = build_boot(1, True).rotate(Axis.X, 90)
    return part.translate((0, 0, -part.bounding_box().min.Z))
