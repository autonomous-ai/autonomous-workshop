# Thickness and hollow

`artifacts/make/r0001/product/assembled.stl --nozzle 0.4 --report artifacts/make/r0001/product/measure/thickness-assembled.md`

artifacts/make/r0001/product/assembled.stl: 59.66 cm3 solid, grid 0.228 mm (418x362x75), 361649 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 361649 samples) |
| thickness distribution | PASS | median 15.85 mm, p95 44.13 mm, max 65.33 mm |
| hollowable at 1.20 mm wall | WARN | 39.51 of 59.66 cm3 (66%) in 3 pocket(s), 2 too small to shell |
| filament that would save | PASS | 5.93 cm3, 7.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
