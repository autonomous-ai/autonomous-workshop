# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_queen.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_queen/r0004/thickness-white_queen.md`

part_white_queen.step.py: 1.81 cm3 solid, grid 0.133 mm (110x110x200), 67371 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 67371 samples) |
| thickness distribution | PASS | median 7.93 mm, p95 20.93 mm, max 26.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.60 of 1.81 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.09 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
