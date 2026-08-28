from build123d import Location
from parts.plectrum import build_plectrum
import params as p
import validation  # noqa: F401

PRINTABLE = True


def gen_step():
    return Location((0, 0, p.PLECTRUM_HEAD_TOP), (180, 0, 0)) * build_plectrum()
