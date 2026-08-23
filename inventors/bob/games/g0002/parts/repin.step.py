"""Re-Pin (g0002) — the combined assembly, in play position.

The lock stands as used: plug at theta = 0, key fully home with settings
1-2-3-4-5, pins of rungs 1-2-3-4-5 in the five chambers (so every chamber is
correct and every pin top sits exactly on the shear radius), five drivers on
those pins, the reset slide at RUN, the latch in its seat.

The hood is placed *off* the shell, on the table beside it — a hood over the
chimneys is what the game looks like in play, but it is not what a build review
can see through, and `inspect interfere` answers a real question either way.
The rest of the kit (case, tray, board, pegs, spare key) lies on the same table
plane, Z = -34.0, which is the shell's foot.

Every placement here is positioning only; all geometry lives in repin_lib.py and
every printed part has its own part_<part_id>.step.py.
"""

import repin_lib as lib

from cadgen.assembly import AssemblyHelper

SETTINGS = (1, 2, 3, 4, 5)
RUNGS_IN = (1, 2, 3, 4, 5)
TABLE = -34.0                      # assembly Z of the table top = the shell foot


def gen_step():
    asm = AssemblyHelper("repin")
    color = lib.part_colors()

    asm.add(lib.asm_shell(), "shell_01", color=color["shell_01"])
    asm.add(lib.asm_plug(0.0), "plug_01", color=color["plug_01"])
    asm.add(lib.asm_cap(), "cap_01", color=color["cap_01"])
    asm.add(lib.asm_latch(), "latch_01", color=color["latch_01"])
    asm.add(lib.asm_lever(0.0), "lever_01", color=color["lever_01"])
    asm.add(lib.asm_key(SETTINGS), "key_01", color=color["key_01"])

    for i, (r, s) in enumerate(zip(RUNGS_IN, SETTINGS)):
        asm.add(lib.asm_pin(i, r, s), f"pin_r{r}", color=color[f"pin_r{r}"])
        asm.add(lib.asm_slug(i, r, s), f"slug_01_{i + 1}", color=color["slug_01"])

    # --- the rest of the kit, on the table ---------------------------------
    asm.add(lib.Pos(30.0, 150.0, TABLE) * lib.print_hood(),
            "hood_01", color=color["hood_01"])
    asm.add(lib.Pos(-95.0, 60.0, TABLE) * lib.print_case(),
            "case_01", color=color["case_01"])
    asm.add(lib.Pos(-93.5, 60.0, TABLE + lib.CASE_T - 3.0 + 0.05) * lib.print_lid(),
            "lid_01", color=color["lid_01"])
    asm.add(lib.Pos(-95.0, -60.0, TABLE) * lib.print_tray(),
            "tray_01", color=color["tray_01"])
    asm.add(lib.Pos(55.0, -110.0, TABLE) * lib.print_board(),
            "board_01", color=color["board_01"])
    for k in range(7):
        asm.add(lib.Pos(-150.0, -40.0 + 10.0 * k, TABLE) * lib.print_peg(),
                f"peg_01_{k + 1}", color=color["peg_01"])

    return asm.compound(label="repin")
