# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0005/parts/chassis.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0005/thickness-chassis.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0005/parts/chassis.stl: 26.83 cm3 solid, grid 0.251 mm (665x239x69), 313397 surface samples, grid resolved to 0.126 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.13, exact where under) | PASS | 0.0% of surface below (0 of 313397 samples) |
| thickness distribution | PASS | median 3.02 mm, p95 21.37 mm, max 165.94 mm |
| hollowable at 1.20 mm wall | WARN | 3.95 of 26.83 cm3 (15%) in 2 pocket(s) |
| filament that would save | PASS | 0.59 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
