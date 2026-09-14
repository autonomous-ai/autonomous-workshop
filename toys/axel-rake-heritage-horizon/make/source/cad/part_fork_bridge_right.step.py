from build123d import Plane,mirror
from parts.fork_bridge import build
from features.common import printed,colored
from params import COLORS
PRINTABLE=True
def gen_step():
    return colored(printed(mirror(build(),about=Plane.XZ),rotation=(-90,0,0)),COLORS['gray'],'fork_bridge_right')
