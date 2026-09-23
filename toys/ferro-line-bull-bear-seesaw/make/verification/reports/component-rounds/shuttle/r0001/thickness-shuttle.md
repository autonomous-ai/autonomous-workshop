# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_shuttle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/shuttle/r0001/thickness-shuttle.md`

part_shuttle.step.py: 5.50 cm3 solid, grid 0.133 mm (1175x290x27), 284544 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 284544 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 16.00 mm, max 156.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.66 of 5.50 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
