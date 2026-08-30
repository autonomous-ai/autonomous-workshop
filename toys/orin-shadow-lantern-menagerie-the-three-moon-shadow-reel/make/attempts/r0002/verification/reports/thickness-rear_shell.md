# Thickness and hollow

`.host-cad-gate-r2b.7VCS7W/project/part_rear_shell.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-rear_shell.md`

.host-cad-gate-r2b.7VCS7W/project/part_rear_shell.stl: 31.92 cm3 solid, grid 0.264 mm (433x471x53), 327673 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 327673 samples); 1043 more within measurement error of the limit |
| thickness distribution | PASS | median 3.17 mm, p95 15.84 mm, max 120.12 mm |
| hollowable at 1.20 mm wall | WARN | 4.85 of 31.92 cm3 (15%) in 8 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.73 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
