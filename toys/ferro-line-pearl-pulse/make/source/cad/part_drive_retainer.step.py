"""Split drive cross-key, flat on its broad side, no assembly transforms."""
from build123d import Rot
from parts.drive import drive_retainer
from features.common import bed
PRINTABLE = True

def gen_step():
    return bed(Rot(0,90,0)*drive_retainer())
