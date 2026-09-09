# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/parts/chassis.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/thickness-chassis.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/parts/chassis.stl: 29.38 cm3 solid, grid 0.251 mm (665x239x69), 331242 surface samples, grid resolved to 0.126 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.13, exact where under) | PASS | 0.0% of surface below (0 of 331242 samples) |
| thickness distribution | PASS | median 3.02 mm, p95 22.88 mm, max 165.94 mm |
| hollowable at 1.20 mm wall | WARN | 4.58 of 29.38 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.69 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
