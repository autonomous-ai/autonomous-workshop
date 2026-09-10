# Thickness and hollow

`artifacts/make/r0001/product/cad/part_king.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-king.md`

artifacts/make/r0001/product/cad/part_king.stl: 24.93 cm3 solid, grid 0.197 mm (155x155x441), 159676 surface samples, grid resolved to 0.098 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.10, exact where under) | PASS | 0.0% of surface below (0 of 159676 samples) |
| thickness distribution | PASS | median 17.93 mm, p95 63.04 mm, max 85.89 mm |
| hollowable at 1.20 mm wall | WARN | 17.55 of 24.93 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 2.63 cm3, 3.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
