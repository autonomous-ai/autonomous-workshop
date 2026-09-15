# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_end_join_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-canopy_end_join_front.md`

part_canopy_end_join_front.step.py: 10.28 cm3 solid, grid 0.228 mm (215x139x356), 134220 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 134220 samples) |
| thickness distribution | PASS | median 3.88 mm, p95 29.87 mm, max 80.04 mm |
| hollowable at 1.20 mm wall | WARN | 2.75 of 10.28 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.41 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
