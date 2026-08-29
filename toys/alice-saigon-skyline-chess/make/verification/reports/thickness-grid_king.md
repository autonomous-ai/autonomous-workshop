# Thickness and hollow

`artifacts/make/r0001/product/cad/part_grid_king.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-grid_king.md`

artifacts/make/r0001/product/cad/part_grid_king.stl: 4.51 cm3 solid, grid 0.133 mm (140x140x417), 145485 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 145485 samples) |
| thickness distribution | PASS | median 7.93 mm, p95 33.73 mm, max 54.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.99 of 4.51 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 0.30 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
