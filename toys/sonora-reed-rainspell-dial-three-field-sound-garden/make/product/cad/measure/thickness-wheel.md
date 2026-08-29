# Thickness and hollow

`project/part_wheel.stl --nozzle 0.4 --report project/measure/thickness-wheel.md`

project/part_wheel.stl: 34.33 cm3 solid, grid 0.277 mm (394x394x68), 245472 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 245472 samples) |
| thickness distribution | PASS | median 6.93 mm, p95 13.86 mm, max 47.26 mm |
| hollowable at 1.20 mm wall | WARN | 16.68 of 34.33 cm3 (49%) in 1 pocket(s), 38 too small to shell |
| filament that would save | PASS | 2.50 cm3, 3.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
