# Thickness and hollow

`artifacts/make/r0001/product/cad/part_board_0_1.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board_0_1.md`

artifacts/make/r0001/product/cad/part_board_0_1.stl: 146.25 cm3 solid, grid 0.291 mm (664x664x26), 382715 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | PASS | 0.0% of surface below (0 of 382715 samples) |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.69 of 146.25 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.20 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
