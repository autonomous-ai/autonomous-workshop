# Thickness and hollow

`artifacts/make/r0001/product/cad/part_outer.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-outer.md`

artifacts/make/r0001/product/cad/part_outer.stl: 64.00 cm3 solid, grid 0.239 mm (672x673x26), 385883 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 385883 samples) |
| thickness distribution | PASS | median 4.91 mm, p95 34.96 mm, max 99.01 mm |
| hollowable at 1.20 mm wall | WARN | 27.51 of 64.00 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 4.13 cm3, 5.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
