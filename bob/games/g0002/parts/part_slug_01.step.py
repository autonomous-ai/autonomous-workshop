"""slug_01 — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

x7 (5 + 2 spare).  Flange-down, 100% infill.
"""

import repin_lib as lib


def gen_step():
    return lib.print_slug()
