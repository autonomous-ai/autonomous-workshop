# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_shaft.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/shaft/r0003/thickness-shaft.md`

part_shaft.step.py: 0.31 cm3 solid, grid 0.133 mm (71x207x29), 24118 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 24118 samples) |
| thickness distribution | PASS | median 3.13 mm, p95 8.73 mm, max 22.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.31 cm3 (3%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
