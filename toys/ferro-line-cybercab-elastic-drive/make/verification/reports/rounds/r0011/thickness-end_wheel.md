# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/end_wheel.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/thickness-end_wheel.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/end_wheel.stl: 5.83 cm3 solid, grid 0.133 mm (252x252x57), 138492 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 138492 samples) |
| thickness distribution | PASS | median 6.93 mm, p95 14.67 mm, max 33.00 mm |
| hollowable at 1.20 mm wall | WARN | 3.13 of 5.83 cm3 (54%) in 1 pocket(s) |
| filament that would save | PASS | 0.47 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
