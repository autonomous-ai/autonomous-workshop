# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/parts/chassis.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/thickness-chassis.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/parts/chassis.stl: 31.28 cm3 solid, grid 0.264 mm (633x228x78), 324834 surface samples, grid resolved to 0.132 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.13, exact where under) | PASS | 0.0% of surface below (0 of 324834 samples) |
| thickness distribution | PASS | median 2.90 mm, p95 19.27 mm, max 165.79 mm |
| hollowable at 1.20 mm wall | WARN | 3.00 of 31.28 cm3 (10%) in 5 pocket(s) |
| filament that would save | PASS | 0.45 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
