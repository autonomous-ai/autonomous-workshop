# Thickness and hollow

`artifacts/make/r0001/product/cad/part_roller_right.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-roller_right.md`

artifacts/make/r0001/product/cad/part_roller_right.stl: 0.41 cm3 solid, grid 0.133 mm (95x95x35), 21491 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 21491 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 4.20 mm, max 4.27 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.41 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
