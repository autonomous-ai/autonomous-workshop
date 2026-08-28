# Thickness and hollow

`artifacts/make/r0001/product/cad/assembled.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-assembled.md`

artifacts/make/r0001/product/cad/assembled.stl: 15.43 cm3 solid, grid 0.140 mm (484x182x133), 239485 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 239485 samples) |
| thickness distribution | PASS | median 12.04 mm, p95 17.92 mm, max 53.27 mm |
| hollowable at 1.20 mm wall | WARN | 10.19 of 15.43 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 1.53 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
