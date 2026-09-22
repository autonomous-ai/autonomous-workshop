"""Mintfin face_sleepy_lid; one physical print, flat bed datum Z=0."""
from parts.face import sleepy_lid
PRINTABLE = True
def gen_step():
    return sleepy_lid()
