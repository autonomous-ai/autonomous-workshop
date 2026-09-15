# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_3.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-return_hood_3.md`

part_return_hood_3.step.py: 35.70 cm3 solid, grid 0.321 mm (486x303x80), 253042 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (0 of 253042 samples); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.89 mm, p95 24.07 mm, max 170.23 mm |
| hollowable at 1.20 mm wall | WARN | 6.26 of 35.70 cm3 (18%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.94 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
