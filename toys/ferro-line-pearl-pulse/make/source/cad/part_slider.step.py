"""Isolated printable slider; print datum Z=0."""
from build123d import Rot
from parts.moving import slider
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(slider(), invert=False)
