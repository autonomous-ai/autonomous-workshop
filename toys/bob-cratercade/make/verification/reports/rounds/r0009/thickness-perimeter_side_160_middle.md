# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_perimeter_side_160_middle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-perimeter_side_160_middle.md`

part_perimeter_side_160_middle.step.py: 19.49 cm3 solid, grid 0.170 mm (81x944x146), 381727 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 381727 samples) |
| thickness distribution | PASS | median 3.91 mm, p95 23.99 mm, max 159.79 mm |
| hollowable at 1.20 mm wall | WARN | 6.42 of 19.49 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 0.96 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
