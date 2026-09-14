# Thickness and hollow

`part_flipper_left_guard_base.step.py --nozzle 0.4 --report measure/thickness-flipper_left_guard_base.md`

part_flipper_left_guard_base.step.py: 18.65 cm3 solid, grid 0.291 mm (504x307x72), 165655 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 165655 samples) |
| thickness distribution | PASS | median 2.91 mm, p95 28.09 mm, max 148.00 mm |
| hollowable at 1.20 mm wall | WARN | 3.52 of 18.65 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
