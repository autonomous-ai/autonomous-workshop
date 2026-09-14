# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_foot_front_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-foot_front_right.md`

part_foot_front_right.step.py: 21.07 cm3 solid, grid 0.188 mm (292x175x210), 287162 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 287162 samples); 114 more within measurement error of the limit |
| thickness distribution | PASS | median 5.91 mm, p95 35.93 mm, max 53.85 mm |
| hollowable at 1.20 mm wall | WARN | 9.81 of 21.07 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 1.47 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
