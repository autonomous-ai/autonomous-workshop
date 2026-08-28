# Thickness and hollow

`cad/part_eye_guard.stl --nozzle 0.4 --report cad/measure/thickness-eye_guard.md`

cad/part_eye_guard.stl: 6.44 cm3 solid, grid 0.133 mm (424x425x27), 285458 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 285458 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 23.67 mm, max 24.80 mm |
| hollowable at 1.20 mm wall | WARN | 1.01 of 6.44 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
