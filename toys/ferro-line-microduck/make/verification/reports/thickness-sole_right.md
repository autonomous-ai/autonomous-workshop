# Thickness and hollow

`artifacts/make/r0001/product/cad/part_sole_right.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-sole_right.md`

artifacts/make/r0001/product/cad/part_sole_right.stl: 1.15 cm3 solid, grid 0.133 mm (260x41x101), 49727 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 49727 samples) |
| thickness distribution | PASS | median 4.73 mm, p95 17.60 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.31 of 1.15 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
