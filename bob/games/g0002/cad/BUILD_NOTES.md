# Re-Pin (g0002) — build notes

Everything is in `games/g0002/parts/`: one `part_<part_id>.step.py` per printed
part, its `.step` and `.stl` beside it, the combined `repin.step.py` assembly,
`part_colors.json`, and `renders/`. Deviations from the brief are in
`cad/DEVIATIONS.md`. Geometry lives in one library, `parts/repin_lib.py`.

**Naming.** The CAD skill's project layout requires `part_<role>.step.py`, so
every file is `part_<part_id>.step.py` / `.step` / `.stl` — `part_plug_01.step.py`
carries `part_id = plug_01`. `part_colors.json` is keyed by the bare `part_id`.

## Print list

**Printed — 14 part ids, 23 files, 67 pieces**

| plate | files | qty | settings (brief §3) |
|---|---|---|---|
| the lock | `plug_01`, `shell_01`, `cap_01`, `latch_01`, `lever_01` | 1 each | plug 0.4/0.20 · shell 0.6/0.30 · latch in **PETG** |
| the guess | `key_01` | **3** (one file, printed 3×) | 0.4/0.20, blade flat, print-in-place |
| the ladder | `pin_r1`…`pin_r8`, `slug_01` | 5 each = 47 pieces, one plate | 0.4/0.20, 100 % infill, pins standing, slugs flange-down |
| the table | `case_01`, `lid_01`, `tray_01`, `board_01`, `peg_01`×7 | | 0.6/0.30 |
| the hood | `hood_01` | 1 | 0.6/0.30, open face down |
| **golden part** | `gp1_plug`, `gp1_shell` | 1 each | **print these first — brief §8** |

**buy_not_print** (brief §3, no geometry by contract): paper deduction pad
(5 × 8, 50 sheets), paper score pad, 4 pencils, folding box 200 × 150 × 90.

## Print first: GP1

`part_gp1_plug.step.py` + `part_gp1_shell.step.py` are cut from the *same*
library functions as the shipping plug and shell, so the test cell tests the
real geometry. Print them, one `slug_01`, all 8 pins and one key, and run the
64-pair test in brief §8. **64/64 → print the rest. ≤62/64 → apply the §5
fallback table and reprint GP1.** No printer ran in this build, so the ladder is
still the 1.2 mm one; the fallback has not been applied.

## Assembly — 6 steps, no tools, no fasteners

1. Press `latch_01` into the shell's seat on the Locksmith flank, nose through
   the window (0.10 interference on four pads).
2. Slide `plug_01` into the shell bore from the rear, pointer flange forward;
   the flange lands on the shell's front face.
3. Snap `cap_01` onto the shell's rear face — three tabs, 1.2 mm engagement.
   The plug now has 0.50 mm of end float and cannot walk out.
4. Slide `lever_01` into the shell's dovetail rails from the rear and click it
   to `LOAD`.
5. Drop the five `slug_01` drivers through the lever's loading holes into the
   chimneys, then the round's five pins through the same holes into the plug's
   bores. Click the lever back to `RUN`.
6. Seat `hood_01` in the shell rebate, open face to the Locksmith.

## Checks that actually ran

Vendored CAD skill at `skills/cad`, interpreter `$BOB_CAD_PY`, one 30-minute
`with_budget` run.

| check | command | result |
|---|---|---|
| layout split rule | `check_layout .` | **ok** — every entry generator conforms |
| build | `gen repin.step.py part_*.step.py --write` | **24/24 built**, STEP written |
| bed + printability of the source | `check_fit .` | **ok — 23 printable parts on the bed, within 220 × 220**; one advisory (project audit) now cleared by `parts/measure/check_fit.py` |
| project fit audit (algebraic) | `$BOB_CAD_PY measure/check_fit.py` | **ok — 63 checks passed**: the three radii, the 8-rung ladder, C1–C14 recomputed from the built constants, every clearance re-derived through `cadfits`, and one part file per `part_id` |
| STEP soundness | `inspect batch` → `validate` × 23 parts + assembly | **0 failures**; assembly reports 28 occurrences, 0 failures |
| mesh | `check_mesh part_*.stl --bed 220x220x250` (final sweep, all 23 STLs re-exported from the finished STEP) | **23/23 printable** — watertight, manifold, consistent winding, positive volume, one shell each (`key_01` is 11 by design: frame + 5 slider bars + 5 lifter rods, print-in-place) |
| clash | `inspect interfere repin.step` | **1 clash, 9.2 mm³: `shell_01` ∩ `latch_01`** — the brief's own press fit ("shell seat — press, 0.10 interference"). No other pair of the 378 clashes. A zero here would mean the latch is loose. |
| motion | `check_motion . --manifest measure/motion.json` | **7 of 8 conditions pass** — table below |

### Motion (8 conditions, `parts/measure/motion.json`)

| condition | expect | result |
|---|---|---|
| `plug-turns-free-0-90` | clear | **ok** — clear across 36 steps, 0–90° |
| `correct-chambers-pass` | clear | **ok** — five correct drivers, plug reaches 90° untouched |
| `key-withdraws` | clear | **ok** — clear across 22 steps, the full 110 mm |
| `plug-captured-rearward` | blocked | **ok** — retained by `shell_01` + `cap_01` |
| `plug-captured-forward` | blocked | **ok** — pointer flange lands on the shell face |
| `cap-captured` | blocked | **ok** — snap tabs hold, 1.2 mm engagement |
| `lever-captured-upward` | blocked | **ok** — dovetail retains the slide |
| `lever-slides-run-to-load` | clear | **FAIL, 0.2175 mm³ — the detent, working.** A rigid sweep cannot represent an elastic snap: the rail nib stands 0.25 mm into the lever flank between positions and the finger deflects past it. Measured directly: **0.000 mm³ at RUN, 0.000 mm³ at LOAD, 0.22–0.72 mm³ in between.** The condition is left in the manifest, and left failing, rather than reworded to pass. |

Three defects were found by these checks and fixed in this build:

- **The key could not go in or come out.** `check_motion` reported
  `key-withdraws` blocked by `plug_01` at step 1 of 22, **612 mm³**: a ⌀4.80
  lifter standing up to 9.8 mm above the blade roof cannot travel 96 mm through
  a keyway roof pierced by only five ⌀5.40 holes. The roof aperture is now one
  continuous ⌀5.40-wide axial slot (DEVIATIONS A5); C13 and C14 are unchanged.
  Re-checked: **clear across all 22 steps.**
- **The plug could not turn.** `plug-turns-free-0-90` blocked by `shell_01` at
  25°, and 61 mm³ of overlap by 45°: the brief's own latch cam lobe reaches
  r 25.0 against a r 22.8 bore. The shell now carries a 7 mm relief band at
  r 25.4 over the cam (DEVIATIONS A6). Re-checked: **clear across 36 steps**,
  and 0.000 mm³ measured at 0 / 25 / 45 / 68 / 90°.
- **`key_01` rods welded to the frame.** `check_mesh` read the printed key as
  **6** connected shells where the design is 11 — the ⌀4.80 lifter head bit
  0.6 mm into a 3.00 mm slot on both sides, fusing all five print-in-place rods.
  Slot thickness is now `max(ROD_T, LIFTER_D) + 2 × gap` = 5.40. Re-checked:
  **11 shells, 0 mm³ of rod↔frame overlap, still printable.**

Two more, found and fixed earlier in the same build:

- **`shell_01` sealed internal void**: the foot, body and skirt webs closed a
  lens-shaped cavity running the full 105 mm and `check_mesh` read 3 shells.
  Ten vent windows open it; re-checked at **1 shell**.
- **The lever detent never clicked**: the rail nib sat 8.4 mm above the flank
  dimples, so it rubbed the dovetail tongue for the whole stroke instead of
  dropping into a dimple — a constant 0.048 mm³ at *every* travel, including the
  seated pose. Nib moved to the dimple height; now 0.000 mm³ at both positions.

## What was not checked

No printer ran, no slicer ran. Print time, filament mass and the §7 20-hour
budget are therefore **unmeasured** — the shell was built as the open ribbed
frame the brief's §7 lever 1 asks for, but no hour claim is made here. The
64-pair GP1 test is a physical test and belongs to the first print.
