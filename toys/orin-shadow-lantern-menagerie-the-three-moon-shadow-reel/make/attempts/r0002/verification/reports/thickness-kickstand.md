# Thickness and hollow

`.host-cad-gate-r2b.7VCS7W/project/part_kickstand.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-kickstand.md`

.host-cad-gate-r2b.7VCS7W/project/part_kickstand.stl: 8.81 cm3 solid, grid 0.207 mm (527x425x48), 147426 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 147426 samples) |
| thickness distribution | PASS | median 4.55 mm, p95 9.93 mm, max 86.87 mm |
| hollowable at 1.20 mm wall | WARN | 2.68 of 8.81 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
