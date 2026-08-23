"""screw_shroud — CLEARANCE (g0003). Contract: ../brief.md §2 gantry_base
(shroud), split into its own part — see ../cad/DEVIATIONS.md.

Print orientation: bed datum at Z = 0.
"""

import clearance_lib as lib


def gen_step():
    return lib.print_screw_shroud()
