"""CLEARANCE (g0003) — the combined assembly, in play position.

The gantry stands at mid-travel (``H_BAR_RENDER``, click 15 of 31), the bar lies
loose in the saddles, the hood hangs from the knob, and one stock rail per seat
carries its six blocks.

Mid-travel, not the top stop, is the render pose for one reason: the screw's
thread and the yoke's nut are two independently generated helices, and they only
mesh where the axial offset is a whole number of pitches. ``H_BAR_RENDER`` is
the mid-travel click that satisfies that, so ``inspect interfere`` is answering a
real question about the fit instead of an artefact of the render pose.

Every placement here is positioning only; all geometry lives in
``clearance_lib.py`` and each printable part has its own ``part_*.step.py``.
"""

import clearance_lib as lib

from cadgen.assembly import AssemblyHelper

H = lib.H_BAR_RENDER
RAIL_Y = (-125.0, -85.0, 85.0, 125.0)


def gen_step():
    asm = AssemblyHelper("clearance")
    color = lib.part_colors()

    asm.add(lib.asm_gantry_base(), "gantry_base", color=color["gantry_base"])
    asm.add(lib.asm_screw_shroud(), "screw_shroud", color=color["screw_shroud"])
    asm.add(lib.asm_column_screw(), "column_screw", color=color["column_screw"])
    asm.add(lib.asm_detent_leaf(), "detent_leaf", color=color["detent_leaf"])
    asm.add(lib.asm_post_guide(), "post_guide", color=color["post_guide"])
    asm.add(lib.asm_stop_ring(), "stop_ring", color=color["stop_ring"])
    asm.add(lib.asm_yoke(H), "yoke", color=color["yoke"])
    asm.add(lib.asm_knob_hood(), "knob_hood", color=color["knob_hood"])
    asm.add(lib.asm_bar(H), "bar_buy_not_print", color=lib.COLORS["bar"])

    for i, letter in enumerate(lib.SETS[:4]):
        y = RAIL_Y[i]
        asm.add(lib.Pos(0, y, 0) * lib.print_rail(), f"rail_{i + 1:02d}",
                color=color[f"rail_{i + 1:02d}"])
        for j in range(6):
            pid = f"piece_{letter}{j + 1}"
            x = (j - 2.5) * lib.POCKET_PITCH
            asm.add(
                lib.Pos(x, y, lib.RAIL_T - lib.POCKET_DEPTH) * lib.print_piece(pid),
                pid, color=color[pid],
            )

    return asm.compound(label="clearance")
