# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-sun.md`

part_sun.step.py: 431.07 cm3 solid, grid 0.474 mm (405x405x64), 266453 surface samples, thickness resolved to 0.237 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.24) | PASS | 0.0% of surface below (0 of 266453 samples) |
| thickness distribution | PASS | median 16.12 mm, p95 179.68 mm, max 184.89 mm |
| hollowable at 1.20 mm wall | WARN | 342.15 of 431.07 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 51.32 cm3, 63.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
