"""piece_e5 — CLEARANCE (g0003). Contract: ../brief.md §2 pieces (H = 16.75 from the nominal H_top; re-sliced per copy, §5.2).

Print orientation: bed datum at Z = 0.
"""

import clearance_lib as lib


def gen_step():
    return lib.print_piece("piece_e5")
