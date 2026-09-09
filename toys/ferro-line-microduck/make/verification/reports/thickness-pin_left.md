# Thickness and hollow

`artifacts/make/r0001/product/cad/part_pin_left.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-pin_left.md`

artifacts/make/r0001/product/cad/part_pin_left.stl: 0.13 cm3 solid, grid 0.133 mm (50x50x90), 10104 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 10104 samples) |
| thickness distribution | PASS | median 3.20 mm, p95 11.33 mm, max 11.33 mm |
| hollowable at 1.20 mm wall | WARN | 0.00 of 0.13 cm3 (3%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
