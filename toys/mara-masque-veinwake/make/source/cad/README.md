# Veinwake CAD

The complete set is `veinwake.step.py`. Its legal draw arrangement contains one rind, five teeth and four bubbles. Printable `part_*.step.py` entries each return one part on its flat bottom; `veinwake_lib.py` holds shared dimensions and geometry.

Overall seated size: 140 × 130 × 32 mm. Every cluster is 28 mm wide and 26 mm tall. Print upright, using a 0.4 mm nozzle on a bed declared as `--bed 220x220x220`. No support or hardware is designed in. Printing and handling have not been physically tested.

Place one cluster in any empty pocket; lift it out to clear the board after play. The open seats have no upward capture. A sampled motion check verifies withdrawal clearance and the floor's downward stop.

`presentation.py` writes exact before/after STEP states. `measure/` contains geometry, rules and manufacturing checks. `snap/` contains canonical product renders and independent review.

Rebuild with the materialized CAD `scripts/gen` command on explicit entry paths and `--write`; use `scripts/verify_project` on this directory with `--strict-fit --print-gates --nozzle 0.4` for full verification.
