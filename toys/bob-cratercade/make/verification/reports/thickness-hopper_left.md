# Thickness and hollow

`part_hopper_left.step.py --nozzle 0.4 --report measure/thickness-hopper_left.md`

part_hopper_left.step.py: 4.06 cm3 solid, grid 0.133 mm (161x560x50), 150031 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 150031 samples); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 19.33 mm, max 58.20 mm |
| hollowable at 1.20 mm wall | WARN | 1.35 of 4.06 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
