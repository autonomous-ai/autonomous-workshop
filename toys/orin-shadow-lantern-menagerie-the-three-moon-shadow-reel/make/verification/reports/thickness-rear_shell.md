# Thickness and hollow

`work/make/r0004/final-clean-r2/part_rear_shell.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-rear_shell.md`

work/make/r0004/final-clean-r2/part_rear_shell.stl: 30.49 cm3 solid, grid 0.264 mm (436x471x53), 322642 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 322642 samples); 1276 more within measurement error of the limit |
| thickness distribution | PASS | median 3.17 mm, p95 19.27 mm, max 120.12 mm |
| hollowable at 1.20 mm wall | WARN | 4.45 of 30.49 cm3 (15%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.67 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
