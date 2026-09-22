"""Mintfin face_happy_mouth; one physical print, flat bed datum Z=0."""
from parts.face import happy_mouth
PRINTABLE = True
def gen_step():
    return happy_mouth()
