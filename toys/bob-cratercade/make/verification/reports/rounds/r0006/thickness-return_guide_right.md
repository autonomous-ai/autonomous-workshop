# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_guide_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-return_guide_right.md`

part_return_guide_right.step.py: 9.33 cm3 solid, grid 0.154 mm (130x575x160), 286577 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 286577 samples) |
| thickness distribution | PASS | median 3.94 mm, p95 23.92 mm, max 34.96 mm |
| hollowable at 1.20 mm wall | WARN | 2.29 of 9.33 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.34 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
