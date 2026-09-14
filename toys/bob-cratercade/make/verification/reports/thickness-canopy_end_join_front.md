# Thickness and hollow

`part_canopy_end_join_front.step.py --nozzle 0.4 --report measure/thickness-canopy_end_join_front.md`

part_canopy_end_join_front.step.py: 11.79 cm3 solid, grid 0.239 mm (205x133x439), 137026 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 137026 samples) |
| thickness distribution | PASS | median 3.95 mm, p95 29.93 mm, max 103.92 mm |
| hollowable at 1.20 mm wall | WARN | 2.81 of 11.79 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.42 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
