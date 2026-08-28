# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_ready_spent_magazine.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-ready_spent_magazine.md`

artifacts/make/r0002/product/cad/comet_heist/part_ready_spent_magazine.stl: 19.73 cm3 solid, grid 0.170 mm (263x428x93), 271736 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 271736 samples) |
| thickness distribution | PASS | median 7.91 mm, p95 71.90 mm, max 71.98 mm |
| hollowable at 1.20 mm wall | WARN | 11.21 of 19.73 cm3 (57%) in 2 pocket(s) |
| filament that would save | PASS | 1.68 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
