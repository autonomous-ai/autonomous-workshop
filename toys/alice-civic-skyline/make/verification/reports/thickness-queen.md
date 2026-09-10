# Thickness and hollow

`artifacts/make/r0001/product/cad/part_queen.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-queen.md`

artifacts/make/r0001/product/cad/part_queen.stl: 23.53 cm3 solid, grid 0.188 mm (162x162x410), 164571 surface samples, grid resolved to 0.094 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 0.0% of surface below (0 of 164571 samples) |
| thickness distribution | PASS | median 18.01 mm, p95 51.03 mm, max 75.98 mm |
| hollowable at 1.20 mm wall | WARN | 16.78 of 23.53 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 2.52 cm3, 3.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
