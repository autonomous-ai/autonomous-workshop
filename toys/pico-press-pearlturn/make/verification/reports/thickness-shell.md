# Thickness and hollow

`artifacts/make/r0001/product/pearlturn/part_shell.stl --nozzle 0.4 --report artifacts/make/r0001/product/pearlturn/measure/thickness-shell.md`

artifacts/make/r0001/product/pearlturn/part_shell.stl: 55.98 cm3 solid, grid 0.228 mm (408x189x136), 309928 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 309928 samples) |
| thickness distribution | PASS | median 9.01 mm, p95 43.21 mm, max 91.90 mm |
| hollowable at 1.20 mm wall | WARN | 38.71 of 55.98 cm3 (69%) in 1 pocket(s) |
| filament that would save | PASS | 5.81 cm3, 7.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
