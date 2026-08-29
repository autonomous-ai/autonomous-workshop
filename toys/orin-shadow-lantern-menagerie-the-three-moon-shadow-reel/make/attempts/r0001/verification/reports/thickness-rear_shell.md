# Thickness and hollow

`artifacts/make/r0001/product/cad/part_rear_shell.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-rear_shell.md`

artifacts/make/r0001/product/cad/part_rear_shell.stl: 24.54 cm3 solid, grid 0.264 mm (433x471x53), 321455 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 321455 samples); 1046 more within measurement error of the limit |
| thickness distribution | PASS | median 2.38 mm, p95 15.18 mm, max 120.12 mm |
| hollowable at 1.20 mm wall | WARN | 0.36 of 24.54 cm3 (1%) in 6 pocket(s), 4 too small to shell |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
