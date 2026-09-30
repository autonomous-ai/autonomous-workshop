# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_mercury_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-world_mercury_sol.md`

part_world_mercury_sol.step.py: 5.62 cm3 solid, grid 0.133 mm (259x259x131), 149900 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 149900 samples) |
| thickness distribution | PASS | median 4.93 mm, p95 33.47 mm, max 33.80 mm |
| hollowable at 1.20 mm wall | WARN | 2.71 of 5.62 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.41 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
