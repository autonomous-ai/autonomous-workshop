# Thickness and hollow

`part_deck_1_1.step.py --nozzle 0.4 --report measure/thickness-deck_1_1.md`

part_deck_1_1.step.py: 170.62 cm3 solid, grid 0.337 mm (479x479x46), 371053 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 371053 samples) |
| thickness distribution | PASS | median 5.90 mm, p95 65.70 mm, max 199.80 mm |
| hollowable at 1.20 mm wall | WARN | 82.77 of 170.62 cm3 (49%) in 1 pocket(s) |
| filament that would save | PASS | 12.42 cm3, 15.4 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
