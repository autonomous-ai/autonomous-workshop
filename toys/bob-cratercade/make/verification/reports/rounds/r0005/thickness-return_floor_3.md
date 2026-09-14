# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_floor_3.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-return_floor_3.md`

part_return_floor_3.step.py: 18.03 cm3 solid, grid 0.188 mm (828x514x26), 303771 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 303771 samples) |
| thickness distribution | PASS | median 3.94 mm, p95 25.98 mm, max 170.26 mm |
| hollowable at 1.20 mm wall | WARN | 6.72 of 18.03 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 1.01 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
