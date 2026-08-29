# Thickness and hollow

`work/make/r0002/determinism-final/part_chassis.stl --nozzle 0.4 --report work/make/r0002/determinism-final/measure/thickness-chassis.md`

work/make/r0002/determinism-final/part_chassis.stl: 11.94 cm3 solid, grid 0.162 mm (338x486x71), 397929 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 397929 samples); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 2.35 mm, p95 38.82 mm, max 77.95 mm |
| hollowable at 1.20 mm wall | WARN | 1.75 of 11.94 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.26 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
