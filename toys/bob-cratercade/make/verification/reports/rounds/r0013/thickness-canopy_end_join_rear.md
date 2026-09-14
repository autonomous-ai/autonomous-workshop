# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_end_join_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0013/thickness-canopy_end_join_rear.md`

part_canopy_end_join_rear.step.py: 11.68 cm3 solid, grid 0.239 mm (205x133x439), 137146 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 137146 samples) |
| thickness distribution | PASS | median 3.95 mm, p95 29.93 mm, max 103.92 mm |
| hollowable at 1.20 mm wall | WARN | 2.67 of 11.68 cm3 (23%) in 1 pocket(s) |
| filament that would save | PASS | 0.40 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
