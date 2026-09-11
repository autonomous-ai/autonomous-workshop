# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0008/thickness-foot_plug.md`

part_foot_plug.step.py: 13.96 cm3 solid, grid 0.140 mm (404x405x73), 317299 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 317299 samples) |
| thickness distribution | PASS | median 5.46 mm, p95 55.93 mm, max 56.00 mm |
| hollowable at 1.20 mm wall | WARN | 6.68 of 13.96 cm3 (48%) in 4 pocket(s) |
| filament that would save | PASS | 1.00 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
