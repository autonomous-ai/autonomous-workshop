"""Isolated printable return_arm; print datum Z=0."""
from build123d import Rot
from parts.moving import return_arm
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(Rot(90,0,0)*return_arm(), invert=False)
