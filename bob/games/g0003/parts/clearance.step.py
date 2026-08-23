"""CLEARANCE (g0003) — the combined assembly, in play position.

The gantry stands at the hard top stop (bar height ``H_TOP_NOM``), the bar
lies loose in the saddles, and one stock rail per seat carries its six blocks.
The knob hood is placed to one side, as it sits on the table between turns.

Every placement here is positioning only; all geometry lives in
``clearance_lib.py`` and each printable part has its own ``part_*.step.py``.
"""

import clearance_lib as lib

from cadgen.assembly import AssemblyHelper

COLORS = {
    "gantry_base": "#B9BFC6",
    "column_screw": "#3F72AF",
    "detent_leaf": "#D64550",
    "post_guide": "#78838F",
    "yoke": "#EDF0F3",
    "stop_ring": "#F0A03C",
    "knob_hood": "#2B303A",
    "bar": "#101418",
    "rail": "#8D6E63",
    "piece": "#DCD5C6",
}

RAIL_Y = (-140.0, -70.0, 0.0, 70.0)


def gen_step():
    asm = AssemblyHelper("clearance")

    asm.add(lib.asm_gantry_base(), "gantry_base", color=COLORS["gantry_base"])
    asm.add(lib.asm_column_screw(), "column_screw", color=COLORS["column_screw"])
    asm.add(lib.asm_detent_leaf(), "detent_leaf", color=COLORS["detent_leaf"])
    asm.add(lib.asm_post_guide(), "post_guide", color=COLORS["post_guide"])
    asm.add(lib.asm_yoke(lib.H_TOP_NOM), "yoke", color=COLORS["yoke"])
    asm.add(lib.asm_stop_ring(), "stop_ring", color=COLORS["stop_ring"])
    asm.add(lib.asm_bar(lib.H_TOP_NOM), "bar_buy_not_print", color=COLORS["bar"])
    asm.add(lib.Pos(-150, 150, 0) * lib.print_knob_hood(),
            "knob_hood", color=COLORS["knob_hood"])

    for i, letter in enumerate(lib.SETS[:4]):
        y = RAIL_Y[i] - 120.0
        asm.add(lib.Pos(0, y, 0) * lib.print_rail(), f"rail_{i + 1:02d}",
                color=COLORS["rail"])
        for j in range(6):
            pid = f"piece_{letter}{j + 1}"
            x = (j - 2.5) * lib.POCKET_PITCH
            asm.add(
                lib.Pos(x, y, lib.RAIL_T - lib.POCKET_DEPTH) * lib.print_piece(pid),
                pid, color=COLORS["piece"],
            )

    return asm.compound(label="clearance")
