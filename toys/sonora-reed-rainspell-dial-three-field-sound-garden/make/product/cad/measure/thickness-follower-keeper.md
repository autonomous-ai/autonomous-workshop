# Thickness and hollow

`artifacts/make/r0001/product/cad/part_follower_keeper.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-follower-keeper.md`

artifacts/make/r0001/product/cad/part_follower_keeper.stl: 0.69 cm3 solid, grid 0.133 mm (335x110x74), 64432 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 64432 samples) |
| thickness distribution | PASS | median 2.00 mm, p95 8.00 mm, max 44.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.69 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
