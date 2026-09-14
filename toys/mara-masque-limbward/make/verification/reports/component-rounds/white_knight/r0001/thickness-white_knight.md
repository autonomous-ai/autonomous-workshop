# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_knight.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_knight/r0001/thickness-white_knight.md`

part_white_knight.step.py: 2.56 cm3 solid, grid 0.133 mm (125x125x185), 71981 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 71981 samples) |
| thickness distribution | PASS | median 10.00 mm, p95 23.93 mm, max 24.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.22 of 2.56 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
