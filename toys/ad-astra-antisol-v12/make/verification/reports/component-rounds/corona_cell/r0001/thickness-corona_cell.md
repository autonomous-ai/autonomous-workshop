# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/corona_cell/r0001/thickness-corona_cell.md`

part_corona_cell.step.py: 3.21 cm3 solid, grid 0.133 mm (256x256x27), 143932 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 143932 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 33.47 mm, max 44.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.37 of 3.21 cm3 (11%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
