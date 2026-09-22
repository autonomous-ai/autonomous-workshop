"""Mintfin face_sleepy_mouth; one physical print, flat bed datum Z=0."""
from parts.face import sleepy_mouth
PRINTABLE = True
def gen_step():
    return sleepy_mouth()
