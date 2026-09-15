# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_king.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_king/r0001/thickness-white_king.md`

part_white_king.step.py: 1.49 cm3 solid, grid 0.133 mm (110x110x215), 55312 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 55312 samples) |
| thickness distribution | PASS | median 7.93 mm, p95 22.93 mm, max 28.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.50 of 1.49 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
