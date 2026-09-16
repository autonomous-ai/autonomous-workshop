# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_ringed_planet.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/square_ringed_planet/r0001/thickness-square_ringed_planet.md`

part_square_ringed_planet.step.py: 3.27 cm3 solid, grid 0.133 mm (170x170x185), 103508 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 103508 samples); 74 more within measurement error of the limit |
| thickness distribution | PASS | median 8.27 mm, p95 22.00 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.27 of 3.27 cm3 (39%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
