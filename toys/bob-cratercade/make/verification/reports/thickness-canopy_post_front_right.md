# Thickness and hollow

`part_canopy_post_front_right.step.py --nozzle 0.4 --report measure/thickness-canopy_post_front_right.md`

part_canopy_post_front_right.step.py: 18.66 cm3 solid, grid 0.147 mm (107x127x808), 378128 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 378128 samples) |
| thickness distribution | PASS | median 3.97 mm, p95 17.93 mm, max 117.97 mm |
| hollowable at 1.20 mm wall | WARN | 5.02 of 18.66 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.75 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
