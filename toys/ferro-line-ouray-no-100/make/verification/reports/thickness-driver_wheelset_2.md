# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_driver_wheelset_2.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-driver_wheelset_2.md`

artifacts/make/r0001/product/cad-project/part_driver_wheelset_2.stl: 0.44 cm3 solid, grid 0.133 mm (83x200x84), 39363 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 39363 samples) |
| thickness distribution | PASS | median 2.00 mm, p95 10.40 mm, max 26.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.44 cm3 (2%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
