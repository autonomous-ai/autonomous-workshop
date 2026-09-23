"""Mintfin face_tongue; one physical print, flat bed datum Z=0."""
from parts.face import tongue
PRINTABLE = True
def gen_step():
    return tongue()
