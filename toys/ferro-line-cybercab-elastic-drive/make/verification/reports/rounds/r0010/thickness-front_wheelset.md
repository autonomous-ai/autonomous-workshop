# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/front_wheelset.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/thickness-front_wheelset.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/front_wheelset.stl: 7.30 cm3 solid, grid 0.197 mm (172x172x391), 113563 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 113563 samples) |
| thickness distribution | PASS | median 6.01 mm, p95 32.90 mm, max 76.04 mm |
| hollowable at 1.20 mm wall | WARN | 2.94 of 7.30 cm3 (40%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
