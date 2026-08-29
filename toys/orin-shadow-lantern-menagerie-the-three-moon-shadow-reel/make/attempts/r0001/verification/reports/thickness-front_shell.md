# Thickness and hollow

`artifacts/make/r0001/product/cad/part_front_shell.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-front_shell.md`

artifacts/make/r0001/product/cad/part_front_shell.stl: 23.36 cm3 solid, grid 0.239 mm (456x518x45), 369188 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 369188 samples) |
| thickness distribution | PASS | median 2.39 mm, p95 18.92 mm, max 131.46 mm |
| hollowable at 1.20 mm wall | WARN | 0.16 of 23.36 cm3 (1%) in 5 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
