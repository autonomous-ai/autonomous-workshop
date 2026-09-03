# Thickness and hollow

`work/make/r0003/host-retry-project/part_front_shell.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-front_shell.md`

work/make/r0003/host-retry-project/part_front_shell.stl: 21.88 cm3 solid, grid 0.251 mm (434x494x49), 330383 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 330383 samples) |
| thickness distribution | PASS | median 2.26 mm, p95 11.06 mm, max 132.12 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 21.88 cm3 (1%) in 5 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
