# Thickness and hollow

`artifacts/make/r0001/product/cad/part_anchor.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-anchor.md`

artifacts/make/r0001/product/cad/part_anchor.stl: 0.20 cm3 solid, grid 0.133 mm (158x110x20), 20759 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 20759 samples) |
| thickness distribution | PASS | median 1.93 mm, p95 7.93 mm, max 14.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.20 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
