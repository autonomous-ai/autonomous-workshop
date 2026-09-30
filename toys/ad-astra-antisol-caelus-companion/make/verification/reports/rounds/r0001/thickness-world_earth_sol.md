# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_earth_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-world_earth_sol.md`

part_world_earth_sol.step.py: 6.67 cm3 solid, grid 0.133 mm (259x259x153), 161360 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 161360 samples) |
| thickness distribution | PASS | median 5.00 mm, p95 33.47 mm, max 33.80 mm |
| hollowable at 1.20 mm wall | WARN | 3.52 of 6.67 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.53 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
