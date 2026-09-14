# Thickness and hollow

`part_foot_front.step.py --nozzle 0.4 --report measure/thickness-foot_front.md`

part_foot_front.step.py: 21.29 cm3 solid, grid 0.188 mm (292x175x204), 284738 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 284738 samples) |
| thickness distribution | PASS | median 6.00 mm, p95 34.90 mm, max 53.85 mm |
| hollowable at 1.20 mm wall | WARN | 10.08 of 21.29 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 1.51 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
