# Thickness and hollow

`part_return_floor_1.step.py --nozzle 0.4 --report measure/thickness-return_floor_1.md`

part_return_floor_1.step.py: 14.11 cm3 solid, grid 0.140 mm (362x932x33), 388544 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 388544 samples) |
| thickness distribution | PASS | median 3.92 mm, p95 26.04 mm, max 129.78 mm |
| hollowable at 1.20 mm wall | WARN | 4.33 of 14.11 cm3 (31%) in 1 pocket(s) |
| filament that would save | PASS | 0.65 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
