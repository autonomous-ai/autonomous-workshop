# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_dust_knot.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_dust_knot/r0002/thickness-circle_dust_knot.md`

part_circle_dust_knot.step.py: 2.57 cm3 solid, grid 0.133 mm (170x170x140), 79225 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 79225 samples) |
| thickness distribution | PASS | median 11.27 mm, p95 21.93 mm, max 22.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.07 of 2.57 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
