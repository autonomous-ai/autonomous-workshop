"""column_screw — CLEARANCE (g0003). Contract: ../brief.md §2 column_screw / §Golden part.

Print orientation: bed datum at Z = 0.
"""

import clearance_lib as lib


def gen_step():
    return lib.print_column_screw()
