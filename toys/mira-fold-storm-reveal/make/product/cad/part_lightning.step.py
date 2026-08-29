"""Printable lightning guide rotor, flat motif on the bed."""

from storm_reveal_lib import build_lightning

PRINTABLE = True
SOURCE_REVISION = "r4-deterministic-monochrome-step"


def gen_step():
    return build_lightning()
