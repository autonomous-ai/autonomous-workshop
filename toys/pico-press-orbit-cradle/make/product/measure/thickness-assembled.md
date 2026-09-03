# Thickness and hollow

`artifacts/make/r0001/product/assembled.stl --nozzle 0.4 --report artifacts/make/r0001/product/measure/thickness-assembled.md`

artifacts/make/r0001/product/assembled.stl: 52.80 cm3 solid, grid 0.228 mm (363x373x84), 284629 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 284629 samples) |
| thickness distribution | PASS | median 17.90 mm, p95 24.51 mm, max 58.95 mm |
| hollowable at 1.20 mm wall | WARN | 36.82 of 52.80 cm3 (70%) in 3 pocket(s), 2 too small to shell |
| filament that would save | PASS | 5.52 cm3, 6.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
