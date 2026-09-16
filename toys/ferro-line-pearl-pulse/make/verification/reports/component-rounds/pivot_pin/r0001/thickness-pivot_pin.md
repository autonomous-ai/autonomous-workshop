# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_pivot_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/pivot_pin/r0001/thickness-pivot_pin.md`

part_pivot_pin.step.py: 0.05 cm3 solid, grid 0.133 mm (41x41x68), 5851 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 5851 samples) |
| thickness distribution | PASS | median 2.33 mm, p95 8.33 mm, max 8.40 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.05 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
