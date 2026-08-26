"""latch_01 — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

PETG.  Flexure bends in the print plane, not across layers.
"""

import repin_lib as lib


def gen_step():
    return lib.print_latch()
