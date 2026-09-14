# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_rear_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-canopy_post_rear_right.md`

part_canopy_post_rear_right.step.py: 11.94 cm3 solid, grid 0.133 mm (117x140x552), 377169 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 377169 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 18.00 mm, max 60.93 mm |
| hollowable at 1.20 mm wall | WARN | 3.38 of 11.94 cm3 (28%) in 2 pocket(s) |
| filament that would save | PASS | 0.51 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
