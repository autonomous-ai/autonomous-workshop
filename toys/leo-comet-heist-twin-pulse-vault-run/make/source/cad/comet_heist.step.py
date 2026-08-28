"""Deployed 24-occurrence Comet Heist assembly; view-only, not one print."""

from build123d import Pos, Rot
from cadgen.assembly import AssemblyHelper
from comet_heist_lib import *

PRINTABLE = False


def gen_step():
    asm = AssemblyHelper("comet_heist_twin_pulse_vault_run")
    # Keep native labels but omit per-occurrence display colours. OpenCascade's
    # STEP writer serializes colour-style associations in hash-table order,
    # which changed otherwise identical assembly bytes across fresh processes.
    # The physical game is single-material and encodes ownership/state in
    # geometry, so display colours are neither a game rule nor a product claim.
    asm.add(Pos(LEFT_TRAY_X, 0, 0) * build_tray_left(), "tray_a")
    asm.add(Pos(RIGHT_TRAY_X, 0, 0) * build_tray_right(), "tray_b")
    for i, x in enumerate((-GATE_X, GATE_X), start=1):
        bridge = build_bridge() if x < 0 else Rot(0, 0, 180) * build_bridge()
        asm.add(Pos(x, 0, FLOOR_T) * bridge, "gate_bridge", i)
        asm.add(Pos(x, 0, PIVOT_Z) * build_blade(), "gravity_blade", i)
        keeper = Pos(x + 9.0, 0, PIVOT_Z - 5.0) * Rot(0, 90, 0) * build_keeper()
        asm.add(keeper, "gate_keeper", i)
    asm.add(Pos(0, -KEY_Y, TRAY_H + 0.2) * build_key(), "seam_storage_key", 1)
    asm.add(Pos(0, KEY_Y, TRAY_H + 0.2) * Rot(0, 0, 180) * build_key(), "seam_storage_key", 2)
    left_mag = Pos(-MAGAZINE_X, 0, 0) * build_magazine()
    right_mag = Pos(MAGAZINE_X, 0, 0) * Rot(0, 0, 180) * build_magazine()
    asm.add(left_mag, "ready_spent_magazine", "sun")
    asm.add(right_mag, "ready_spent_magazine", "orbit")
    for side, x, builder in (("sun", -MAGAZINE_X, build_comet_sun),
                             ("orbit", MAGAZINE_X, build_comet_orbit)):
        for well_y in (-18.0, 18.0):
            for level in range(3):
                z = MAG_H + level * (COMET_T + RELIEF_H + 0.3)
                asm.add(Pos(x, well_y, z) * builder(), f"{side}_comet", f"{well_y:+.0f}", level + 1)
    return asm.build()
