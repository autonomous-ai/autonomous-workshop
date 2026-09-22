# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0006/thickness-body_01_front.md`

part_body_01_front.step.py: 1.97 cm3 solid, grid 0.133 mm (436x241x82), 158757 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 158757 samples); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 12.33 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 1.97 cm3 (11%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
