from build123d import Plane,mirror
from parts.chassis_half import build
from features.common import printed,colored
from params import COLORS
PRINTABLE=True
def gen_step():
    return colored(printed(mirror(build(),about=Plane.XZ),rotation=(-90,0,0)),COLORS['charcoal'],'chassis_half_right')
