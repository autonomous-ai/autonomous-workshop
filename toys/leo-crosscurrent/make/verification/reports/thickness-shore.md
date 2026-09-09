# Thickness and hollow

`artifacts/make/r0001/product/cad/part_shore.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-shore.md`

artifacts/make/r0001/product/cad/part_shore.stl: 140.00 cm3 solid, grid 0.306 mm (691x692x24), 384710 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 384710 samples) |
| thickness distribution | PASS | median 3.97 mm, p95 5.81 mm, max 209.95 mm |
| hollowable at 1.20 mm wall | WARN | 51.83 of 140.00 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 7.77 cm3, 9.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
