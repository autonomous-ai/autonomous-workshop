# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_northeast.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/panel_northeast/r0002/thickness-panel_northeast.md`

part_panel_northeast.step.py: 203.45 cm3 solid, grid 0.306 mm (502x620x34), 378919 surface samples, thickness resolved to 0.153 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 378919 samples); 4070 more within measurement error of the limit |
| thickness distribution | PASS | median 8.86 mm, p95 116.59 mm, max 187.95 mm |
| hollowable at 1.20 mm wall | WARN | 123.93 of 203.45 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 18.59 cm3, 23.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
