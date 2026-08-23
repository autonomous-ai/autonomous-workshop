# Millbind — build spec

Source of truth: `board-game/ideas/millbind/idea.json` + `brief.json` +
`brief.md`. This file is a short pointer, not a restatement.

A hexagonal yard (`yard_board`) bristling with 37 pins on one shared
triangular lattice carries real, physically meshing gears at two tooth
heights: `gear_low` (teeth at the floor) and `gear_high` (teeth at the top of
a smooth column). `gear_tandem` is the only supply piece with teeth the full
pin height, so it is the only piece that can bridge the two tiers. Four
millstones (`mill_gear_tri/square/penta/hex`) are told apart only by their
prism hub's flat count — a player's whole identity, read by counting flats,
never by colour. `crank_gear` is the only piece with an arm, a knurled knob
and a direction arrow — the only power in the box, relocating every round.
`grain_pellet` washers thread onto each player's `sack_spindle`; the loose
supply lives in `granary_bin`.

## Build-mode scope

The full bill, every component a separately named `cq.Assembly` child:
1x yard_board, 14x gear_low, 7x gear_high, 3x gear_tandem, 1x each of the
four millstones, 1x crank_gear, 28x grain_pellet, 4x sack_spindle,
1x granary_bin = 63 named parts.

`validation.py` hard-asserts every bill number from brief.json onto
`Params` before a render is attempted. `fit_checks.py` re-measures the
actually exported STLs for every `## Interfaces` entry: the partial-engagement
pin/bore fit (gear_low), the full-engagement pin/bore fit (representative of
gear_high / gear_tandem / all four millstones / crank_gear), the
tooth-to-tooth mesh geometry (root/pitch/outer radii against the shared
30mm pin pitch), and the rod/hole pellet-on-spindle fit + stack capacity.

## Position discipline

`features/lattice.hex_lattice_positions` is the ONE 37-point triangular
lattice generator in the project — centre + ring of 6 + ring of 12 + ring of
18 at `pin_pitch` spacing. `parts/board.py` cuts the pins and the 18-pin
sill ring from it; `assemblies/product.py` places every staged supply gear,
millstone and the crank from the SAME list. No second copy of this trig
exists anywhere in the project.

## Fidelity additions beyond the draft

The build adds the brief's `1mm chevron water-texture` relief (declared as
`relief_mm: 1.0` in brief.json for both `sack_spindle` and `granary_bin`,
absent from the fast draft) as a genuine cut feature: alternating-tilt
V-groove notches around the spindle base skirt, and a zigzag ribbon groove
across the bin's front wall. Silhouette is otherwise unchanged from the
approved draft in `board-game/ideas/millbind/reference/`.
