# Thickness and hollow

`part_access_lever.step.py --nozzle 0.4 --report measure/thickness-access_lever.md`

part_access_lever.step.py: 1.88 cm3 solid, grid 0.133 mm (95x245x65), 71547 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 71547 samples) |
| thickness distribution | PASS | median 5.20 mm, p95 13.20 mm, max 32.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.61 of 1.88 cm3 (32%) in 2 pocket(s) |
| filament that would save | PASS | 0.09 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
