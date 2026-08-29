# Thickness and hollow

`artifacts/make/r0001/product/cad/part_grid_rook.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-grid_rook.md`

artifacts/make/r0001/product/cad/part_grid_rook.stl: 2.91 cm3 solid, grid 0.133 mm (140x140x260), 97130 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 97130 samples) |
| thickness distribution | PASS | median 9.93 mm, p95 18.00 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.25 of 2.91 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
