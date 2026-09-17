from features.forms import bed_on_z
from parts.lower_leg_armor import build


def gen_step():
    return bed_on_z(build(), (90, 0, 0))
