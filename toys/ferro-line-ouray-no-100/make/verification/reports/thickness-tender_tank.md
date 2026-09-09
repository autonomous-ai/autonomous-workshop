# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_tank.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_tank.md`

artifacts/make/r0001/product/cad-project/part_tender_tank.stl: 51.00 cm3 solid, grid 0.179 mm (312x185x184), 302338 surface samples, thickness resolved to 0.089 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 302338 samples) |
| thickness distribution | PASS | median 31.98 mm, p95 54.85 mm, max 54.85 mm |
| hollowable at 1.20 mm wall | WARN | 39.42 of 51.00 cm3 (77%) in 1 pocket(s) |
| filament that would save | PASS | 5.91 cm3, 7.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
