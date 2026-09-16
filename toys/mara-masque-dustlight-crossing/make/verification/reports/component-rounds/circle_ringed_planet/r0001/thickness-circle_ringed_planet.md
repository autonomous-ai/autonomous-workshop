# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_ringed_planet.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_ringed_planet/r0001/thickness-circle_ringed_planet.md`

part_circle_ringed_planet.step.py: 2.99 cm3 solid, grid 0.133 mm (170x170x185), 92824 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 92824 samples); 72 more within measurement error of the limit |
| thickness distribution | PASS | median 9.53 mm, p95 22.00 mm, max 24.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.21 of 2.99 cm3 (40%) in 1 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
