# Thickness and hollow

`cad/part_crank_arm.stl --nozzle 0.4 --report cad/measure/thickness-crank_arm.md`

cad/part_crank_arm.stl: 6.35 cm3 solid, grid 0.188 mm (179x309x203), 112512 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 112512 samples) |
| thickness distribution | PASS | median 3.94 mm, p95 25.98 mm, max 57.60 mm |
| hollowable at 1.20 mm wall | WARN | 2.42 of 6.35 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.36 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
