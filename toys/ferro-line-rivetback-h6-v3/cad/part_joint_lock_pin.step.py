from features.forms import bed_on_z
from parts.joint_lock_pin import build


def gen_step():
    return bed_on_z(build())
