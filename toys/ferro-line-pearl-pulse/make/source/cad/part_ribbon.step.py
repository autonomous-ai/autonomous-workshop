"""Isolated printable ribbon; print datum Z=0."""
from build123d import Rot
from parts.moving import ribbon
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(ribbon(), invert=False)
