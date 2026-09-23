# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_beam.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-beam.md`

part_beam.step.py: 21.83 cm3 solid, grid 0.162 mm (1165x140x67), 341801 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 341801 samples) |
| thickness distribution | PASS | median 10.05 mm, p95 11.99 mm, max 188.00 mm |
| hollowable at 1.20 mm wall | WARN | 12.56 of 21.83 cm3 (58%) in 3 pocket(s) |
| filament that would save | PASS | 1.88 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
