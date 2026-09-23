# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_06_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_06_front/r0002/thickness-body_06_front.md`

part_body_06_front.step.py: 1.78 cm3 solid, grid 0.133 mm (208x178x78), 77078 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 77078 samples) |
| thickness distribution | PASS | median 3.47 mm, p95 23.13 mm, max 27.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.33 of 1.78 cm3 (19%) in 2 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
