from parts.swingarm_side import build
from features.common import printed,colored
from params import COLORS
PRINTABLE=True
def gen_step():
    return colored(printed(build()),COLORS['gray'],'swingarm_side')
