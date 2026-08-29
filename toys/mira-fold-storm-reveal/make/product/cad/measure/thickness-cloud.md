# Thickness and hollow

`project/part_cloud.stl --nozzle 0.4 --report project/measure/thickness-cloud.md`

project/part_cloud.stl: 27.10 cm3 solid, grid 0.154 mm (568x426x44), 398705 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 398705 samples) |
| thickness distribution | PASS | median 6.02 mm, p95 66.22 mm, max 92.69 mm |
| hollowable at 1.20 mm wall | WARN | 14.28 of 27.10 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 2.14 cm3, 2.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
