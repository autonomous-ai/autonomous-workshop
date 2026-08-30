# Thickness and hollow

`work/make/r0003/host-retry-project/part_shadow_reel.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-shadow_reel.md`

work/make/r0003/host-retry-project/part_shadow_reel.stl: 12.43 cm3 solid, grid 0.170 mm (675x675x24), 393911 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 393911 samples) |
| thickness distribution | PASS | median 3.23 mm, p95 16.68 mm, max 60.16 mm |
| hollowable at 1.20 mm wall | WARN | 1.74 of 12.43 cm3 (14%) in 2 pocket(s), 9 too small to shell |
| filament that would save | PASS | 0.26 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
