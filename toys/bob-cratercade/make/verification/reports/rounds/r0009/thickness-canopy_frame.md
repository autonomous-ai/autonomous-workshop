# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-canopy_frame.md`

part_canopy_frame.step.py: 41.02 cm3 solid, grid 0.277 mm (581x523x35), 253480 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 253480 samples) |
| thickness distribution | PASS | median 7.48 mm, p95 16.08 mm, max 159.66 mm |
| hollowable at 1.20 mm wall | WARN | 20.88 of 41.02 cm3 (51%) in 1 pocket(s) |
| filament that would save | PASS | 3.13 cm3, 3.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
