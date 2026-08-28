# Thickness and hollow

`project/part_cap.stl --nozzle 0.4 --report project/measure/thickness-cap.md`

project/part_cap.stl: 7.18 cm3 solid, grid 0.133 mm (244x245x119), 227919 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 227919 samples); 92 more within measurement error of the limit |
| thickness distribution | PASS | median 8.07 mm, p95 10.80 mm, max 15.20 mm |
| hollowable at 1.20 mm wall | WARN | 3.53 of 7.18 cm3 (49%) in 1 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
