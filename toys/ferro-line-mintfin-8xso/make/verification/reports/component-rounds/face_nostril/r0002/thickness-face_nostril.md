# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_nostril.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_nostril/r0002/thickness-face_nostril.md`

part_face_nostril.step.py: 0.00 cm3 solid, grid 0.133 mm (17x17x12), 500 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 500 samples) |
| thickness distribution | PASS | median 1.53 mm, p95 1.60 mm, max 1.67 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.00 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
