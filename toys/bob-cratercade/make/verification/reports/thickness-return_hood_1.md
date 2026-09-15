# Thickness and hollow

`part_return_hood_1.step.py --nozzle 0.4 --report measure/thickness-return_hood_1.md`

part_return_hood_1.step.py: 29.91 cm3 solid, grid 0.251 mm (204x521x100), 332924 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 332924 samples) |
| thickness distribution | PASS | median 3.14 mm, p95 26.02 mm, max 129.73 mm |
| hollowable at 1.20 mm wall | WARN | 6.32 of 29.91 cm3 (21%) in 1 pocket(s) |
| filament that would save | PASS | 0.95 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
