# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_stand.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/stand/r0001/thickness-stand.md`

part_stand.step.py: 30.28 cm3 solid, grid 0.277 mm (243x411x114), 129827 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 129827 samples) |
| thickness distribution | PASS | median 9.98 mm, p95 60.57 mm, max 112.54 mm |
| hollowable at 1.20 mm wall | WARN | 19.64 of 30.28 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 2.95 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
