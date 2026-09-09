# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/rear_wheelset.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/thickness-rear_wheelset.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/rear_wheelset.stl: 8.04 cm3 solid, grid 0.197 mm (172x172x388), 95716 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 95716 samples) |
| thickness distribution | PASS | median 6.89 mm, p95 33.00 mm, max 75.45 mm |
| hollowable at 1.20 mm wall | WARN | 4.09 of 8.04 cm3 (51%) in 1 pocket(s) |
| filament that would save | PASS | 0.61 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
