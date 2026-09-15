# Thickness and hollow

`part_canopy_post_rear_left.step.py --nozzle 0.4 --report measure/thickness-canopy_post_rear_left.md`

part_canopy_post_rear_left.step.py: 16.25 cm3 solid, grid 0.133 mm (117x140x732), 378418 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 378418 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 18.00 mm, max 84.93 mm |
| hollowable at 1.20 mm wall | WARN | 4.54 of 16.25 cm3 (28%) in 2 pocket(s) |
| filament that would save | PASS | 0.68 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
