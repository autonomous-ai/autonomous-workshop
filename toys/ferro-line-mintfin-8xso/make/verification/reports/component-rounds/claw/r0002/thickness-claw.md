# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_claw.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/claw/r0002/thickness-claw.md`

part_claw.step.py: 0.06 cm3 solid, grid 0.133 mm (38x46x38), 4664 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 4664 samples) |
| thickness distribution | PASS | median 4.07 mm, p95 5.40 mm, max 6.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.00 of 0.06 cm3 (5%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
