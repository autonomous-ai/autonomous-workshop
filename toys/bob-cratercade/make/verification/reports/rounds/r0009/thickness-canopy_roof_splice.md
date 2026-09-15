# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_roof_splice.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-canopy_roof_splice.md`

part_canopy_roof_splice.step.py: 7.90 cm3 solid, grid 0.133 mm (365x285x62), 316048 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 316048 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 36.00 mm, max 48.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.15 of 7.90 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.32 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
