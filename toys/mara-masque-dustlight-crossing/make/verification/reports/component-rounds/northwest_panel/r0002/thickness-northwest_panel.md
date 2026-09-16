# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_northwest_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/northwest_panel/r0002/thickness-northwest_panel.md`

part_northwest_panel.step.py: 73.04 cm3 solid, grid 0.197 mm (492x797x30), 373125 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 373125 samples); 482 more within measurement error of the limit |
| thickness distribution | PASS | median 4.92 mm, p95 95.84 mm, max 156.02 mm |
| hollowable at 1.20 mm wall | WARN | 35.18 of 73.04 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 5.28 cm3, 6.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
