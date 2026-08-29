# Thickness and hollow

`artifacts/make/r0001/product/cad/part_river_rook.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-river_rook.md`

artifacts/make/r0001/product/cad/part_river_rook.stl: 2.61 cm3 solid, grid 0.133 mm (140x140x260), 85825 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 85825 samples) |
| thickness distribution | PASS | median 10.00 mm, p95 18.00 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.15 of 2.61 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
