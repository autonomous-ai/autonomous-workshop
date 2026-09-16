# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_support.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/support/r0002/thickness-support.md`

part_support.step.py: 16.98 cm3 solid, grid 0.321 mm (185x185x307), 108157 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (0 of 108157 samples) |
| thickness distribution | PASS | median 5.13 mm, p95 23.75 mm, max 93.38 mm |
| hollowable at 1.20 mm wall | WARN | 5.85 of 16.98 cm3 (34%) in 2 pocket(s) |
| filament that would save | PASS | 0.88 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
