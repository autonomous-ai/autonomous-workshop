# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_southeast.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-panel_southeast.md`

part_panel_southeast.step.py: 169.48 cm3 solid, grid 0.277 mm (553x553x37), 380107 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 380107 samples) |
| thickness distribution | PASS | median 8.87 mm, p95 151.76 mm, max 157.72 mm |
| hollowable at 1.20 mm wall | WARN | 110.47 of 169.48 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 16.57 cm3, 20.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
