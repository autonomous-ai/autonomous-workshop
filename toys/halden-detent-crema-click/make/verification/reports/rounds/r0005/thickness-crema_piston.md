# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_crema_piston.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0005/thickness-crema_piston.md`

part_crema_piston.step.py: 12.06 cm3 solid, grid 0.188 mm (239x239x207), 145269 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 145269 samples) |
| thickness distribution | PASS | median 4.88 mm, p95 43.90 mm, max 44.09 mm |
| hollowable at 1.20 mm wall | WARN | 6.33 of 12.06 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.95 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
