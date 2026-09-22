# Shatterline CAD

The complete set is `veinwake.step.py`. Its legal draw arrangement contains one rind, five teeth and four bubbles. Printable `part_*.step.py` entries each return one part on its flat bottom; `veinwake_lib.py` holds shared dimensions and geometry. The file names keep the original project's spelling so the unchanged tooth exports stay byte-identical to the source archive.

Overall seated size: 140 × 130 × 32 mm. Every marker is 28 mm wide and 26 mm tall. Print upright, using a 0.4 mm nozzle on a bed declared as `--bed 220x220x220`. No support or hardware is designed in. Printing and handling have not been physically tested.

This revision replaces two of the three unique geometries. `make_rind()` builds a low-polygon fractured boulder: a sixteen-segment angular plan, sixteen flat outer wall facets at 8–25° from vertical, a thirty-two triangle faceted cavity wall, and no spline, fillet or round-over anywhere. `make_bubble()` builds a pyrite-habit cluster of five interpenetrating cubes of unequal edge on the unchanged circular foot. `make_tooth()` is untouched.

Place one marker in any empty pocket; lift it out to clear the board after play. The open seats have no upward capture. The operator selected `check_motion: false` for this run, so no motion sweep or animation was produced and motion is unverified, never passed.

`presentation.py` writes exact before/after STEP states. `render_exact.py` writes the canonical `snap/` renders, including the overhead pair used for the state-legibility check. `measure/` contains geometry, rules, wall, lineage and manufacturing checks. `ref/` holds the two read-only Wish reference images.

Rebuild with the materialized CAD `scripts/gen` command on explicit entry paths and `--write`; use `scripts/verify_project` on this directory with `--strict-fit --print-gates --nozzle 0.4` for full verification.
