from features.forms import bed_on_z
from parts.dorsal_center import build


def gen_step():
    return bed_on_z(build())
