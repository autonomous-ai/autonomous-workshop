# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_perimeter_side_152_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-perimeter_side_152_right.md`

part_perimeter_side_152_right.step.py: 19.09 cm3 solid, grid 0.170 mm (81x897x146), 380393 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 380393 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 23.99 mm, max 151.79 mm |
| hollowable at 1.20 mm wall | WARN | 5.99 of 19.09 cm3 (31%) in 1 pocket(s) |
| filament that would save | PASS | 0.90 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
