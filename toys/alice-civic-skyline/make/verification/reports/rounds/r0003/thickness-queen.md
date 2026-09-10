# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/queen.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-queen.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/queen.stl: 23.46 cm3 solid, grid 0.188 mm (162x162x410), 165726 surface samples, grid resolved to 0.094 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 0.0% of surface below (0 of 165726 samples) |
| thickness distribution | PASS | median 17.92 mm, p95 51.03 mm, max 75.98 mm |
| hollowable at 1.20 mm wall | WARN | 16.70 of 23.46 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 2.50 cm3, 3.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
