# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_horn_middle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/horn_middle/r0001/thickness-horn_middle.md`

part_horn_middle.step.py: 0.31 cm3 solid, grid 0.133 mm (65x65x117), 14366 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 14366 samples) |
| thickness distribution | PASS | median 7.00 mm, p95 9.07 mm, max 14.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.09 of 0.31 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
