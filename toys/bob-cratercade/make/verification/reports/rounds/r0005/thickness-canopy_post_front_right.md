# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_front_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-canopy_post_front_right.md`

part_canopy_post_front_right.step.py: 14.29 cm3 solid, grid 0.133 mm (117x140x710), 379394 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 379394 samples) |
| thickness distribution | PASS | median 3.93 mm, p95 18.00 mm, max 87.13 mm |
| hollowable at 1.20 mm wall | WARN | 3.62 of 14.29 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.54 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
