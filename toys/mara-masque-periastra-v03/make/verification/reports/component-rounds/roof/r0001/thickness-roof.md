# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_roof.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/roof/r0001/thickness-roof.md`

part_roof.step.py: 972.38 cm3 solid, grid 0.667 mm (278x278x137), 246643 surface samples, thickness resolved to 0.334 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.33) | PASS | 0.0% of surface below (0 of 246643 samples); 7 more within measurement error of the limit |
| thickness distribution | PASS | median 34.36 mm, p95 74.71 mm, max 245.49 mm |
| hollowable at 1.20 mm wall | WARN | 819.75 of 972.38 cm3 (84%) in 1 pocket(s), 4 too small to shell |
| filament that would save | PASS | 122.96 cm3, 152.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
