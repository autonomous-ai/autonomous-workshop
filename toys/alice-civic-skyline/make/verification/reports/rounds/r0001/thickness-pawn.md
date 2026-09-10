# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/pawn.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-pawn.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/pawn.stl: 8.62 cm3 solid, grid 0.133 mm (185x185x305), 156066 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 156066 samples) |
| thickness distribution | PASS | median 16.87 mm, p95 24.00 mm, max 40.00 mm |
| hollowable at 1.20 mm wall | WARN | 5.45 of 8.62 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 0.82 cm3, 1.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
