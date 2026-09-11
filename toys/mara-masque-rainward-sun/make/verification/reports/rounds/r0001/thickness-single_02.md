# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_single_02.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-single_02.md`

part_single_02.step.py: 0.26 cm3 solid, grid 0.133 mm (95x65x35), 13408 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 13408 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 11.93 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.05 of 0.26 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
