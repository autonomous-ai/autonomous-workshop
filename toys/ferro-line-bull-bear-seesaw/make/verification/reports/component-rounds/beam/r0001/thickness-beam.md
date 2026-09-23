# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_beam.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/beam/r0001/thickness-beam.md`

part_beam.step.py: 20.89 cm3 solid, grid 0.162 mm (1165x140x67), 347271 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 347271 samples) |
| thickness distribution | PASS | median 10.05 mm, p95 25.53 mm, max 188.00 mm |
| hollowable at 1.20 mm wall | WARN | 11.57 of 20.89 cm3 (55%) in 3 pocket(s) |
| filament that would save | PASS | 1.74 cm3, 2.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
