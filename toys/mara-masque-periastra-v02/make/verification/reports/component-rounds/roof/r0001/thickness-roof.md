# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_roof.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/roof/r0001/thickness-roof.md`

part_roof.step.py: 859.96 cm3 solid, grid 0.576 mm (321x321x102), 272247 surface samples, thickness resolved to 0.288 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.29) | PASS | 0.0% of surface below (0 of 272247 samples); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 32.56 mm, p95 84.71 mm, max 245.49 mm |
| hollowable at 1.20 mm wall | WARN | 745.66 of 859.96 cm3 (87%) in 1 pocket(s) |
| filament that would save | PASS | 111.85 cm3, 138.7 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
