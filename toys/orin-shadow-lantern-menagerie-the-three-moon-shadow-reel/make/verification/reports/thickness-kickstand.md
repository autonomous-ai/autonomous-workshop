# Thickness and hollow

`work/make/r0004/final-clean-r2/part_kickstand.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-kickstand.md`

work/make/r0004/final-clean-r2/part_kickstand.stl: 8.22 cm3 solid, grid 0.197 mm (553x393x50), 151551 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 151551 samples) |
| thickness distribution | PASS | median 4.53 mm, p95 17.98 mm, max 76.53 mm |
| hollowable at 1.20 mm wall | WARN | 2.67 of 8.22 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
