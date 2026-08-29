"""Printable rainbow drive rotor, flat motif on the bed."""

from storm_reveal_lib import build_rainbow

PRINTABLE = True
SOURCE_REVISION = "r4-deterministic-monochrome-step"


def gen_step():
    return build_rainbow()
