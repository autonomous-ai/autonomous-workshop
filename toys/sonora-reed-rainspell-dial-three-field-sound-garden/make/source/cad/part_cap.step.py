from build123d import Location
from parts.cap import build_cap
import params as p
import validation  # noqa: F401

PRINTABLE = True


def gen_step():
    # In-use flat top down; print transform maps top z=15.25 to bed z=0.
    return Location((0, 0, p.CAP_TOP_Z - p.CAP_BOTTOM_Z), (180, 0, 0)) * build_cap()
