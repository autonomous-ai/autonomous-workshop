# Thickness and hollow

`artifacts/make/r0001/product/cad/part_board.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board.md`

artifacts/make/r0001/product/cad/part_board.stl: 144.78 cm3 solid, grid 0.277 mm (755x755x19), 398757 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 398757 samples) |
| thickness distribution | PASS | median 3.46 mm, p95 3.88 mm, max 207.89 mm |
| hollowable at 1.20 mm wall | WARN | 45.70 of 144.78 cm3 (32%) in 1 pocket(s) |
| filament that would save | PASS | 6.86 cm3, 8.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
