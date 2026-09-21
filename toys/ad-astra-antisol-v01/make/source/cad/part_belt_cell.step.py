"""One asteroid-belt tile -- twelve of these make the water.

Four-fold symmetric, so any tile goes in any belt cell either way round.  The
landing pad and every crest a seated disc can touch finish at the field datum,
so a piece standing in the belt stands level.
"""

from parts.belt import build_belt_cell

PRINTABLE = True


def gen_step():
    return build_belt_cell()
