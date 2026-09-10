# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/parts/board_1_0.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-board_1_0.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/parts/board_1_0.stl: 146.24 cm3 solid, grid 0.291 mm (664x664x26), 384553 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | PASS | 0.0% of surface below (0 of 384553 samples) |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.73 of 146.24 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.21 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
