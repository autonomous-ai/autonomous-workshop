"""Mintfin face_eye; one physical print, flat bed datum Z=0."""
from parts.face import eye
PRINTABLE = True
def gen_step():
    return eye()
