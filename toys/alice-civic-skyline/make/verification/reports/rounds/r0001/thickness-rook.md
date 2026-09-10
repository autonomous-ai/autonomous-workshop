# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/rook.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-rook.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/rook.stl: 21.53 cm3 solid, grid 0.154 mm (184x184x342), 236983 surface samples, grid resolved to 0.077 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.08, exact where under) | PASS | 0.0% of surface below (0 of 236983 samples) |
| thickness distribution | PASS | median 18.99 mm, p95 48.93 mm, max 52.02 mm |
| hollowable at 1.20 mm wall | WARN | 14.83 of 21.53 cm3 (69%) in 1 pocket(s) |
| filament that would save | PASS | 2.23 cm3, 2.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
