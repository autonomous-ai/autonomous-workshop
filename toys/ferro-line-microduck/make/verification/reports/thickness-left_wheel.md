# Thickness and hollow

`artifacts/make/r0001/product/cad/part_left_wheel.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-left_wheel.md`

artifacts/make/r0001/product/cad/part_left_wheel.stl: 1.54 cm3 solid, grid 0.133 mm (155x155x50), 56774 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 56774 samples) |
| thickness distribution | PASS | median 5.93 mm, p95 6.00 mm, max 6.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.52 of 1.54 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
