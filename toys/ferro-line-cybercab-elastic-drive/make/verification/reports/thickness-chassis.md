# Thickness and hollow

`artifacts/make/r0001/product/cybercab/part_chassis.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-chassis.md`

artifacts/make/r0001/product/cybercab/part_chassis.stl: 26.64 cm3 solid, grid 0.251 mm (665x239x69), 315429 surface samples, grid resolved to 0.126 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.13, exact where under) | PASS | 0.0% of surface below (0 of 315429 samples) |
| thickness distribution | PASS | median 3.02 mm, p95 21.37 mm, max 165.94 mm |
| hollowable at 1.20 mm wall | WARN | 3.75 of 26.64 cm3 (14%) in 2 pocket(s) |
| filament that would save | PASS | 0.56 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
