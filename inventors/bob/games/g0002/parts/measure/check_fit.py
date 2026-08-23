"""Re-Pin (g0002) — the project's own fit/print audit.

Algebraic only: it asserts the shared base dimensions, every derived clearance,
the brief's C1-C15 coupled-dimension checks and the part-file inventory. It
builds no geometry — solids, bodies, meshes and bed fit belong to
``scripts/check_fit``, ``scripts/inspect validate`` and ``scripts/check_mesh``,
and are not re-litigated here.

Run:  $BOB_CAD_PY measure/check_fit.py      (from games/g0002/parts)
Exit 0 = every check passed; the failing assertion names itself otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
# cadfits ships with the vendored CAD skill; scripts/gen puts it on the path
# for the generators, so a standalone run has to do the same.
sys.path.insert(0, str(_HERE.parents[2] / "skills" / "cad" / "scripts"))

import cadfits
import repin_lib as lib

OK: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    assert cond, f"FAIL {name} — {detail}"
    OK.append(f"ok  {name:38s} {detail}")


# --- 1. the three radii, the whole mechanism -------------------------------
check("radii ordered", lib.R_PLUG < lib.R_SHEAR < lib.R_BORE,
      f"{lib.R_PLUG} < {lib.R_SHEAR} < {lib.R_BORE}")
check("C4 shear gap symmetric",
      abs((lib.R_SHEAR - lib.R_PLUG) - (lib.R_BORE - lib.R_SHEAR)) < 1e-6,
      f"0.40 each side")

# --- 2. the ladder ---------------------------------------------------------
check("ladder is 8 rungs", len(lib.PIN_HEIGHTS) == 8, str(lib.PIN_HEIGHTS))
check("ladder step 1.2",
      all(abs(b - a - lib.LADDER_STEP) < 1e-9
          for a, b in zip(lib.PIN_HEIGHTS, lib.PIN_HEIGHTS[1:])), "1.2 mm")
check("C1 bore working length",
      abs(lib.B_WORK - 12.80) < 1e-6, f"B = {lib.B_WORK}")
check("C2 tallest pin + shortest lifter fills B [DEV A3: from the blade roof 9.00]",
      abs(lib.BLADE_ROOF_Y + lib.LIFTER_H[-1] + lib.PIN_HEIGHTS[-1] - lib.R_SHEAR) < 1e-6,
      f"9.00 + {lib.LIFTER_H[-1]} + {lib.PIN_HEIGHTS[-1]} = {lib.R_SHEAR}")
check("C3 lifter travel = ladder span",
      abs(lib.LIFTER_TRAVEL - lib.LADDER_STEP * 7) < 1e-6,
      f"{lib.LIFTER_TRAVEL} = 7 x 1.2")
check("s == r puts the pin top on the shear radius",
      all(abs(lib.LIFTER_TOP_Y[s - 1] + lib.PIN_HEIGHTS[s - 1] - lib.R_SHEAR) < 1e-9
          for s in range(1, lib.RUNGS + 1)), "all 8 settings")

# --- 3. the ordinal contract ----------------------------------------------
check("stops strictly increasing",
      all(b > a for a, b in zip(lib.STOPS, lib.STOPS[1:])), str(lib.STOPS))
check("5 chambers at 16.0 pitch",
      len(lib.CHAMBER_X) == 5 and all(
          abs(b - a - lib.CHAMBER_PITCH) < 1e-9
          for a, b in zip(lib.CHAMBER_X, lib.CHAMBER_X[1:])), str(lib.CHAMBER_X))
check("C10 pitch clears the feature width",
      lib.CHAMBER_PITCH - lib.BORE_D >= 9.0, f"{lib.CHAMBER_PITCH - lib.BORE_D:.2f}")

# --- 4. every clearance is derived, never typed twice ----------------------
check("pin in plug bore = 0.35 radial",
      abs(cadfits.peg_for(lib.BORE_D, lib.PIN_CLEAR_RADIAL) - lib.PIN_D) < 1e-6,
      f"{lib.PIN_D} in {lib.BORE_D}")
check("driver nose in guide bore = 0.35 radial",
      abs(cadfits.peg_for(lib.GUIDE_BORE_D, lib.PIN_CLEAR_RADIAL) - lib.SLUG_NOSE_D) < 1e-6,
      f"{lib.SLUG_NOSE_D} in {lib.GUIDE_BORE_D}")
check("driver flange in counterbore = 0.35 radial",
      abs(cadfits.peg_for(lib.COUNTERBORE_D, lib.COUNTERBORE_CLEAR) - lib.SLUG_FLANGE_D) < 1e-6,
      f"{lib.SLUG_FLANGE_D} in {lib.COUNTERBORE_D}")
check("plug journal in shell cradle = 0.30 radial",
      abs(cadfits.peg_for(lib.CRADLE_D, lib.JOURNAL_CLEAR) - lib.JOURNAL_D) < 1e-6,
      f"{lib.JOURNAL_D} in {lib.CRADLE_D}")
check("peg in socket = 0.20 per side",
      abs(cadfits.slot_for(lib.PEG_D, 0.20) - lib.SOCKET_D) < 1e-6,
      f"{lib.PEG_D} in {lib.SOCKET_D}")
check("blade in keyway = 0.30 per side",
      abs((lib.KEYWAY_W - lib.BLADE_W) / 2 - 0.30) < 1e-9
      and abs((lib.KEYWAY_H - lib.BLADE_H) / 2 - 0.30) < 1e-6,
      f"{lib.BLADE_W}x{lib.BLADE_H} in {lib.KEYWAY_W}x{lib.KEYWAY_H}")
check("dovetail transition 0.20 total",
      abs(2 * lib.DOVETAIL_FIT - 0.20) < 1e-6, "0.10 per side")
check("C14 lifter passes the roof aperture",
      lib.APERTURE_D - lib.LIFTER_D - 0.30 >= 0.29,
      f"{lib.LIFTER_D} + 0.30 play in {lib.APERTURE_D}")
check("C13 pin cannot fall through the aperture",
      lib.PIN_D - lib.APERTURE_D >= 0.79, f"{lib.PIN_D} vs {lib.APERTURE_D}")

# --- 5. the coupled dimensions that decide the mechanism -------------------
check("C5 one-rung engagement",
      abs((lib.LADDER_STEP - (lib.R_SHEAR - lib.R_PLUG)) - 0.80) < 1e-6,
      "1.2 - 0.4 = 0.80")
check("C6 notch floor clears the keyway roof corner [DEV depth 2.00]",
      lib.NOTCH_FLOOR_R - 13.10 >= 5.50, f"{lib.NOTCH_FLOOR_R} vs r 13.10")
check("C7 channel swallows the max over-stack",
      lib.CHANNEL_DEPTH >= lib.LADDER_STEP * 7, f"{lib.CHANNEL_DEPTH} >= 8.40")
check("C8 material between channel roof and shoulder",
      abs(lib.SHOULDER_R - lib.CHANNEL_OUTER_R - 2.40) < 1e-6, "2.40")
check("C9 keyway corners inside the plug",
      (lib.KEYWAY_W / 2) ** 2 + max(abs(lib.KEYWAY_ROOF_Y), abs(lib.KEYWAY_FLOOR_Y)) ** 2
      < lib.R_PLUG ** 2, "corner r < 22.0")
check("C11 blade reaches chamber 5",
      lib.BLADE_LEN - lib.CHAMBER_X[-1] >= 8.0, f"{lib.BLADE_LEN} vs 88")
check("C12 driver body = shoulder - shear",
      abs(lib.DRIVER_BODY - 12.20) < 1e-6, "12.20")
check("shell keeps >= 3.0 solid outside the channels [brief §6, blind]",
      lib.BODY_OUTER_R - lib.CHANNEL_OUTER_R >= 3.0,
      f"{lib.BODY_OUTER_R - lib.CHANNEL_OUTER_R:.2f}")
check("ogive roof stays under the shoulder datum [DEV 45 deg flanks]",
      lib.OGIVE_APEX_R < lib.SHOULDER_R,
      f"apex {lib.OGIVE_APEX_R:.2f} < {lib.SHOULDER_R}")
check("ogive roof clears the plug land by >= 1.0",
      lib.OGIVE_TANGENT_R - lib.R_PLUG >= 1.0,
      f"{lib.OGIVE_TANGENT_R - lib.R_PLUG:.2f}")

# --- 6. the reset slide lives inside one chamber pitch [DEV] ---------------
check("lever travel + ramp inside one pitch",
      lib.LEVER_DETENTS[1] + lib.LEVER_LAND < lib.CHAMBER_PITCH,
      f"{lib.LEVER_DETENTS[1]} + {lib.LEVER_LAND} < {lib.CHAMBER_PITCH}")
check("lever lift frees every driver nose",
      lib.LEVER_TOP_Y - lib.SLUG_HEAD_BOT >= lib.R_SHEAR,
      f"nose lands at {lib.LEVER_TOP_Y - lib.SLUG_HEAD_BOT}")
check("lever tunnel clears the tallest possible head",
      lib.LEVER_ROOF_Y >= lib.LEVER_TOP_Y + lib.SLUG_HEAD_L + lib.LEVER_RISE_MAX,
      f"roof {lib.LEVER_ROOF_Y}")
check("lever fits under the hood ceiling",
      lib.LEVER_ROOF_Y + 2.5 <= lib.HOOD_CEIL_Y, f"{lib.HOOD_CEIL_Y}")
check("cap end float 0.50 axial",
      abs(lib.CAP_END_FLOAT - 0.50) < 1e-6, f"{lib.CAP_END_FLOAT}")

# --- 7. key lanes and print-in-place gaps ---------------------------------
g = lib.PIP["xy"]
check("key lane webs >= 0.55",
      lib.LANE_X[1] - lib.LANE_X[0] - (lib.LANE_W + 2 * g) >= 0.55,
      f"{lib.LANE_X[1] - lib.LANE_X[0] - (lib.LANE_W + 2 * g):.2f}")
check("key outer walls >= 0.95",
      (lib.BLADE_W - (lib.LANE_X[-1] - lib.LANE_X[0]) - (lib.LANE_W + 2 * g)) / 2 >= 0.95,
      f"{(lib.BLADE_W - (lib.LANE_X[-1] - lib.LANE_X[0]) - (lib.LANE_W + 2 * g)) / 2:.2f}")
check("slider pitch 4.00, travel 28.0",
      abs(lib.SLIDER_PITCH - 4.0) < 1e-9 and abs(lib.SLIDER_TRAVEL - 28.0) < 1e-6,
      "as briefed")

# --- 8. part inventory: one file per part_id, named to match ---------------
PART_IDS = ["plug_01", "shell_01", "cap_01", "hood_01", "latch_01", "lever_01",
            "slug_01", "case_01", "lid_01", "key_01", "tray_01", "board_01",
            "peg_01"] + [f"pin_r{r}" for r in range(1, 9)]
here = Path(__file__).resolve().parent.parent
for pid in PART_IDS:
    check(f"part file for {pid}", (here / f"part_{pid}.step.py").is_file(),
          f"part_{pid}.step.py")
check("golden part files present",
      (here / "part_gp1_plug.step.py").is_file()
      and (here / "part_gp1_shell.step.py").is_file(), "GP1 plug + shell")
check("combined assembly entry present", (here / "repin.step.py").is_file(),
      "repin.step.py")
check("colour map covers every part_id",
      all(pid in lib.part_colors() for pid in PART_IDS), "part_colors.json")

# --- 9. bed ----------------------------------------------------------------
check("brief bed limit is 251 cubed", lib.BED == 251.0,
      "geometric bed fit is scripts/check_fit's job, not this file's")

print("\n".join(OK))
print(f"\ncheck_fit(project): ok - {len(OK)} algebraic checks passed")
