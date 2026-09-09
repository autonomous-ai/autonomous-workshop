# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/front_wheelset.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/thickness-front_wheelset.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/front_wheelset.stl: 7.74 cm3 solid, grid 0.197 mm (172x172x388), 92652 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 92652 samples) |
| thickness distribution | PASS | median 6.89 mm, p95 33.00 mm, max 75.45 mm |
| hollowable at 1.20 mm wall | WARN | 3.93 of 7.74 cm3 (51%) in 1 pocket(s) |
| filament that would save | PASS | 0.59 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
