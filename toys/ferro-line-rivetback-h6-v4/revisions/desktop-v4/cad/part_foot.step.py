from features.forms import bed_on_z
from parts.foot import build


def gen_step():
    return bed_on_z(build())
