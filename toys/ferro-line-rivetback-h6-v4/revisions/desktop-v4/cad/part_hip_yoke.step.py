from features.forms import bed_on_z
from parts.hip_yoke import build


def gen_step():
    return bed_on_z(build(), (0, 90, 0))
