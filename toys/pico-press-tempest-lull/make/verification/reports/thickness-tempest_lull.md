# Thickness and hollow

`artifacts/make/r0001/product/cad/tempest_lull.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-tempest_lull.md`

artifacts/make/r0001/product/cad/tempest_lull.stl: 81.54 cm3 solid, grid 0.228 mm (412x84x320), 341968 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 341968 samples) |
| thickness distribution | PASS | median 18.02 mm, p95 48.92 mm, max 92.81 mm |
| hollowable at 1.20 mm wall | WARN | 61.96 of 81.54 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 9.29 cm3, 11.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
