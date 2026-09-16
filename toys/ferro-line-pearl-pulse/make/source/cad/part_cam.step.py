"""Isolated printable cam; print datum Z=0."""
from build123d import Rot
from parts.drive import cam
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(cam(), invert=True)
