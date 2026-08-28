# Thickness and hollow

`artifacts/make/r0001/product/cad/part_grid_bishop.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-grid_bishop.md`

artifacts/make/r0001/product/cad/part_grid_bishop.stl: 3.12 cm3 solid, grid 0.133 mm (140x140x325), 111995 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 111995 samples) |
| thickness distribution | PASS | median 6.93 mm, p95 26.73 mm, max 42.67 mm |
| hollowable at 1.20 mm wall | WARN | 1.29 of 3.12 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
