"""hood_01 — Re-Pin (g0002).

Contract: ../parts_brief.md §3.  Deviations: ../cad/DEVIATIONS.md.

Print on the open (Locksmith) face: every wall vertical.
"""

import repin_lib as lib


def gen_step():
    return lib.print_hood()
