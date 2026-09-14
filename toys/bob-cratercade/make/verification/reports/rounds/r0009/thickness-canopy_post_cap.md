# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-canopy_post_cap.md`

part_canopy_post_cap.step.py: 4.89 cm3 solid, grid 0.133 mm (207x285x114), 197983 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 197983 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 29.20 mm, max 36.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.38 of 4.89 cm3 (28%) in 3 pocket(s) |
| filament that would save | PASS | 0.21 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
