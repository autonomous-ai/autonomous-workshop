# Thickness and hollow

`cad/part_brace.stl --nozzle 0.4 --report cad/measure/thickness-brace.md`

cad/part_brace.stl: 7.89 cm3 solid, grid 0.133 mm (260x440x35), 262485 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 262485 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 57.93 mm, max 58.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.81 of 7.89 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.42 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
