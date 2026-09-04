# Gutterfall

Parametric STEP-first CAD for one printable rigid gargoyle.
`gutterfall_v7_lib.py` owns the final parameters and geometry;
`gutterfall_final.step.py` is the sole combined printable entry.

Verified envelope: 113 x 84 x 62 mm. Print as the combined entry in its
provided bed orientation on a 220 x 220 x 220 mm bed with a 0.4 mm nozzle.
Supports may be needed beneath the chin and swept wings depending on slicer;
the continuous belly-tail load path is intentionally broad and contains no
pins, stored energy, or loose components.

Rebuild with the run-materialized CAD scripts: run `gen` on
`gutterfall_final.step.py` with `--write`, export `gutterfall_final.step` to
STL, then run
`verify_project` with `--print-preflight` before visual review and once without
that flag for final verification.
