"""post_guide — CLEARANCE (g0003). Contract: ../brief.md §2 post_guide.

Print orientation: bed datum at Z = 0.
"""

import clearance_lib as lib


def gen_step():
    return lib.print_post_guide()
