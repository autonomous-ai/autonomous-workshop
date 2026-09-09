# Thickness and hollow

`artifacts/make/r0001/product/cad/part_dark_lens.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-dark_lens.md`

artifacts/make/r0001/product/cad/part_dark_lens.stl: 0.34 cm3 solid, grid 0.133 mm (74x74x44), 15477 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 15477 samples) |
| thickness distribution | PASS | median 9.07 mm, p95 9.20 mm, max 9.27 mm |
| hollowable at 1.20 mm wall | WARN | 0.10 of 0.34 cm3 (28%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
