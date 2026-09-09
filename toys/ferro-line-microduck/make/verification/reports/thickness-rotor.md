# Thickness and hollow

`artifacts/make/r0001/product/cad/part_rotor.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-rotor.md`

artifacts/make/r0001/product/cad/part_rotor.stl: 4.61 cm3 solid, grid 0.147 mm (141x141x527), 199501 surface samples, grid resolved to 0.074 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 199501 samples) |
| thickness distribution | PASS | median 1.47 mm, p95 8.67 mm, max 69.16 mm |
| hollowable at 1.20 mm wall | WARN | 0.89 of 4.61 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.13 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
