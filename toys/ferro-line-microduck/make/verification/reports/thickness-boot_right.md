# Thickness and hollow

`artifacts/make/r0001/product/cad/part_boot_right.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boot_right.md`

artifacts/make/r0001/product/cad/part_boot_right.stl: 2.80 cm3 solid, grid 0.133 mm (260x80x101), 79248 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 79248 samples) |
| thickness distribution | PASS | median 10.00 mm, p95 18.93 mm, max 34.40 mm |
| hollowable at 1.20 mm wall | WARN | 1.34 of 2.80 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
