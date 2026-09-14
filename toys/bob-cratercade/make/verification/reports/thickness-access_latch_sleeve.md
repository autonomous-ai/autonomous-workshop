# Thickness and hollow

`part_access_latch_sleeve.step.py --nozzle 0.4 --report measure/thickness-access_latch_sleeve.md`

part_access_latch_sleeve.step.py: 0.36 cm3 solid, grid 0.133 mm (87x87x87), 30899 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 30899 samples) |
| thickness distribution | PASS | median 1.27 mm, p95 10.93 mm, max 10.93 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.36 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
