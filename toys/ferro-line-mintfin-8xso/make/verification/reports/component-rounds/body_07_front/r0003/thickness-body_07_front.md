# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_front/r0003/thickness-body_07_front.md`

part_body_07_front.step.py: 0.68 cm3 solid, grid 0.133 mm (150x141x71), 44010 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 44010 samples) |
| thickness distribution | PASS | median 1.20 mm, p95 9.27 mm, max 17.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.68 cm3 (21%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
