"""Isolated printable cup; print datum Z=0."""
from build123d import Rot
from parts.drive import cup
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(cup(), invert=False)
