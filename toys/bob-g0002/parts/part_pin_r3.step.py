"""pin_r3 — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

x5.  Rung 3: height 5.4 +-0.10 — the tightest number in the game.
"""

import repin_lib as lib


def gen_step():
    return lib.bed(lib.build_pin(3))
