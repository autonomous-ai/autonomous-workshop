# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_perimeter_side_152.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-perimeter_side_152.md`

part_perimeter_side_152.step.py: 18.78 cm3 solid, grid 0.170 mm (81x897x146), 380427 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 380427 samples) |
| thickness distribution | PASS | median 3.91 mm, p95 23.99 mm, max 151.79 mm |
| hollowable at 1.20 mm wall | WARN | 5.69 of 18.78 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.85 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
