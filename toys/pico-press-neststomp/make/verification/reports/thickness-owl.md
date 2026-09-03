# Thickness and hollow

`artifacts/make/r0001/product/neststomp/part_owl.stl --nozzle 0.4 --report artifacts/make/r0001/product/neststomp/measure/thickness-owl.md`

artifacts/make/r0001/product/neststomp/part_owl.stl: 68.45 cm3 solid, grid 0.228 mm (303x356x110), 271421 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 271421 samples) |
| thickness distribution | PASS | median 23.94 mm, p95 64.42 mm, max 68.30 mm |
| hollowable at 1.20 mm wall | WARN | 53.12 of 68.45 cm3 (78%) in 1 pocket(s) |
| filament that would save | PASS | 7.97 cm3, 9.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
