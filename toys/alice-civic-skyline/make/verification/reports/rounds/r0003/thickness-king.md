# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/king.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-king.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/king.stl: 24.87 cm3 solid, grid 0.197 mm (155x155x441), 160712 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 160712 samples) |
| thickness distribution | PASS | median 16.94 mm, p95 63.04 mm, max 85.89 mm |
| hollowable at 1.20 mm wall | WARN | 17.47 of 24.87 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 2.62 cm3, 3.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
