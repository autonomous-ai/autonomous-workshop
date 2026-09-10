# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/king.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-king.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/king.stl: 23.44 cm3 solid, grid 0.197 mm (155x155x441), 156387 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 156387 samples) |
| thickness distribution | PASS | median 16.94 mm, p95 58.90 mm, max 85.89 mm |
| hollowable at 1.20 mm wall | WARN | 16.36 of 23.44 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 2.45 cm3, 3.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
