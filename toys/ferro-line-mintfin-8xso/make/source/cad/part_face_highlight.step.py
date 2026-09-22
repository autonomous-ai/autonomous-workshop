"""Mintfin face_highlight; one physical print, flat bed datum Z=0."""
from parts.face import highlight
PRINTABLE = True
def gen_step():
    return highlight()
