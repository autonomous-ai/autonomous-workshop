"""stop_ring — CLEARANCE (g0003). Contract: ../brief.md §2 stop_ring / §5.3.

Print orientation: bed datum at Z = 0.
"""

import clearance_lib as lib


def gen_step():
    return lib.print_stop_ring()
