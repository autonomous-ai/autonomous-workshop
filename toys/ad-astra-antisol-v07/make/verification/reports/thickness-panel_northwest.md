# Thickness and hollow

`part_panel_northwest.step.py --nozzle 0.4 --report measure/thickness-panel_northwest.md`

part_panel_northwest.step.py: 157.78 cm3 solid, grid 0.277 mm (423x683x37), 379343 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 379343 samples) |
| thickness distribution | PASS | median 8.87 mm, p95 115.87 mm, max 187.94 mm |
| hollowable at 1.20 mm wall | WARN | 102.29 of 157.78 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 15.34 cm3, 19.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
