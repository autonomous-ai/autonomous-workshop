"""pin_r7 — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

x5.  Rung 7: height 10.2 +-0.10 — the tightest number in the game.
"""

import repin_lib as lib


def gen_step():
    return lib.bed(lib.build_pin(7))
