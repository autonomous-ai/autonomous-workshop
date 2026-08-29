# Thickness and hollow

`artifacts/make/r0003/product-candidate/cad/part_rear_shell.stl --nozzle 0.4 --voxel 0.16 --report artifacts/make/r0003/product-candidate/cad/measure/thickness-rear_shell-fine.md`

artifacts/make/r0003/product-candidate/cad/part_rear_shell.stl: 31.80 cm3 solid, grid 0.261 mm (442x477x54), 340961 surface samples, thickness resolved to 0.130 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 340961 samples); 1345 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 16.03 mm, max 120.15 mm |
| hollowable at 1.20 mm wall | WARN | 4.76 of 31.80 cm3 (15%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.71 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
