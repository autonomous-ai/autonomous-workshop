# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_roof.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-roof.md`

part_roof.step.py: 997.17 cm3 solid, grid 0.667 mm (278x278x137), 236391 surface samples, thickness resolved to 0.334 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.33) | PASS | 0.0% of surface below (0 of 236391 samples); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 35.36 mm, p95 149.43 mm, max 245.49 mm |
| hollowable at 1.20 mm wall | WARN | 851.81 of 997.17 cm3 (85%) in 1 pocket(s) |
| filament that would save | PASS | 127.77 cm3, 158.4 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
