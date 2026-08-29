# Thickness and hollow

`artifacts/make/r0001/product/cad/part_river_queen.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-river_queen.md`

artifacts/make/r0001/product/cad/part_river_queen.stl: 3.54 cm3 solid, grid 0.133 mm (140x140x372), 116311 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 116311 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 18.00 mm, max 48.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.53 of 3.54 cm3 (43%) in 2 pocket(s) |
| filament that would save | PASS | 0.23 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
