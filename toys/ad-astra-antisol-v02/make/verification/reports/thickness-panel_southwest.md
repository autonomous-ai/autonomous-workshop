# Thickness and hollow

`cad/part_panel_southwest.step.py --nozzle 0.4 --report cad/measure/thickness-panel_southwest.md`

part_panel_southwest.step.py: 137.17 cm3 solid, grid 0.251 mm (466x609x41), 380609 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 380609 samples) |
| thickness distribution | PASS | median 8.93 mm, p95 115.90 mm, max 151.86 mm |
| hollowable at 1.20 mm wall | WARN | 86.46 of 137.17 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 12.97 cm3, 16.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
