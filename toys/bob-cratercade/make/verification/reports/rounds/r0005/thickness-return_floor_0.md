# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_floor_0.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-return_floor_0.md`

part_return_floor_0.step.py: 13.80 cm3 solid, grid 0.162 mm (557x649x29), 318256 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 318256 samples) |
| thickness distribution | PASS | median 3.89 mm, p95 28.85 mm, max 127.63 mm |
| hollowable at 1.20 mm wall | WARN | 4.98 of 13.80 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.75 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
