"""Deployed Storm Reveal assembly; not a one-piece print target."""

from build123d import Compound
from storm_reveal_lib import build_assembly

PRINTABLE = False
SOURCE_REVISION = "r4-deterministic-monochrome-step"


def gen_step():
    built = build_assembly()
    return Compound(label="storm_reveal", children=built.children)
