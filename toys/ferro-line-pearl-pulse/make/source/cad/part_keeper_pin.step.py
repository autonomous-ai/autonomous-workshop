"""Isolated printable keeper_pin; print datum Z=0."""
from build123d import Rot
from parts.moving import keeper_pin
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(keeper_pin(), invert=False)
