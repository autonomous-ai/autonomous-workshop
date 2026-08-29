# Thickness and hollow

`artifacts/make/r0001/product/cad/part_river_king.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-river_king.md`

artifacts/make/r0001/product/cad/part_river_king.stl: 4.22 cm3 solid, grid 0.133 mm (140x140x417), 134150 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 134150 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 33.73 mm, max 54.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.89 of 4.22 cm3 (45%) in 1 pocket(s) |
| filament that would save | PASS | 0.28 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
