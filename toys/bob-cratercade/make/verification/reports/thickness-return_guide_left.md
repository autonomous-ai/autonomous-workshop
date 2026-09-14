# Thickness and hollow

`part_return_guide_left.step.py --nozzle 0.4 --report measure/thickness-return_guide_left.md`

part_return_guide_left.step.py: 10.77 cm3 solid, grid 0.239 mm (297x339x105), 131657 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 131657 samples) |
| thickness distribution | PASS | median 3.95 mm, p95 23.94 mm, max 36.40 mm |
| hollowable at 1.20 mm wall | WARN | 2.92 of 10.77 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
