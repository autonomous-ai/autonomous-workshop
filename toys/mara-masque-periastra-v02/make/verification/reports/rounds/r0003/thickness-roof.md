# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_roof.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-roof.md`

part_roof.step.py: 860.44 cm3 solid, grid 0.576 mm (321x321x102), 275729 surface samples, thickness resolved to 0.288 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.29) | PASS | 0.0% of surface below (0 of 275729 samples); 16 more within measurement error of the limit |
| thickness distribution | PASS | median 34.58 mm, p95 72.32 mm, max 245.49 mm |
| hollowable at 1.20 mm wall | WARN | 744.60 of 860.44 cm3 (87%) in 1 pocket(s) |
| filament that would save | PASS | 111.69 cm3, 138.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
