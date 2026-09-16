"""Isolated shaft, printed on its common broad Y=-1.6 face."""
from build123d import Rot
from parts.drive import shaft
from features.common import bed
PRINTABLE = True

def gen_step():
    return bed(Rot(90,0,0)*shaft())
