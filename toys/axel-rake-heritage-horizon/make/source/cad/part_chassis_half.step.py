from parts.chassis_half import build
from features.common import printed,colored
from params import COLORS
PRINTABLE=True
def gen_step():
    return colored(printed(build()),COLORS['charcoal'],'chassis_half')
