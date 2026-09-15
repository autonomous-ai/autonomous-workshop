# Thickness and hollow

`part_return_hood_0.step.py --nozzle 0.4 --report measure/thickness-return_hood_0.md`

part_return_hood_0.step.py: 28.81 cm3 solid, grid 0.277 mm (335x381x91), 261234 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 261234 samples) |
| thickness distribution | PASS | median 3.19 mm, p95 23.84 mm, max 99.65 mm |
| hollowable at 1.20 mm wall | WARN | 6.93 of 28.81 cm3 (24%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 1.04 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
