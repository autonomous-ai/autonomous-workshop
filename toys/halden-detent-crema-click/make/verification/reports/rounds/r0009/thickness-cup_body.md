# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0009/thickness-cup_body.md`

part_cup_body.step.py: 100.85 cm3 solid, grid 0.277 mm (286x236x165), 264721 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 264721 samples) |
| thickness distribution | PASS | median 20.51 mm, p95 44.35 mm, max 46.71 mm |
| hollowable at 1.20 mm wall | WARN | 76.43 of 100.85 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 11.47 cm3, 14.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
