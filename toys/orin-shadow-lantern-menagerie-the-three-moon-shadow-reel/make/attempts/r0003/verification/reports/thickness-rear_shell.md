# Thickness and hollow

`work/make/r0003/host-retry-project/part_rear_shell.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-rear_shell.md`

work/make/r0003/host-retry-project/part_rear_shell.stl: 32.17 cm3 solid, grid 0.264 mm (436x471x53), 332183 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 332183 samples); 1274 more within measurement error of the limit |
| thickness distribution | PASS | median 3.17 mm, p95 15.97 mm, max 120.12 mm |
| hollowable at 1.20 mm wall | WARN | 4.85 of 32.17 cm3 (15%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.73 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
