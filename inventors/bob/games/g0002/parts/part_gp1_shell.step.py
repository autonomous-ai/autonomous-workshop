"""gp1_shell — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

GOLDEN PART (brief §8), not a shipped part.
"""

import repin_lib as lib


def gen_step():
    return lib.print_gp1_shell()
