"""Mintfin face_nostril; one physical print, flat bed datum Z=0."""
from parts.face import nostril
PRINTABLE = True
def gen_step():
    return nostril()
