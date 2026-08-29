# Thickness and hollow

`artifacts/make/r0002/product/cad/part_rear_shell.stl --nozzle 0.4 --voxel 0.16 --report artifacts/make/r0002/product/cad/measure/thickness-rear_shell-fine.md`

artifacts/make/r0002/product/cad/part_rear_shell.stl: 31.54 cm3 solid, grid 0.261 mm (438x477x54), 336020 surface samples, thickness resolved to 0.130 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 336020 samples); 1061 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 15.77 mm, max 120.15 mm |
| hollowable at 1.20 mm wall | WARN | 4.79 of 31.54 cm3 (15%) in 7 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.72 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
