# Thickness and hollow

`part_launch_divider_upper.step.py --nozzle 0.4 --report measure/thickness-launch_divider_upper.md`

part_launch_divider_upper.step.py: 12.66 cm3 solid, grid 0.170 mm (113x673x146), 259436 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 259436 samples) |
| thickness distribution | PASS | median 3.91 mm, p95 23.99 mm, max 113.67 mm |
| hollowable at 1.20 mm wall | WARN | 4.44 of 12.66 cm3 (35%) in 1 pocket(s) |
| filament that would save | PASS | 0.67 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
