from build123d import Location
from parts.follower_keeper import build_follower_keeper
import validation  # noqa: F401

PRINTABLE = True


def gen_step():
    shape = Location((-15.5, 7.0, 0)) * build_follower_keeper()
    return shape
