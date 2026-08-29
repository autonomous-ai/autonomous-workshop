# Thickness and hollow

`work/make/r0002/determinism-final/part_left_wing.stl --nozzle 0.4 --report work/make/r0002/determinism-final/measure/thickness-left_wing.md`

work/make/r0002/determinism-final/part_left_wing.stl: 1.65 cm3 solid, grid 0.133 mm (167x422x27), 98190 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 98190 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 19.67 mm, max 24.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.18 of 1.65 cm3 (11%) in 2 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
