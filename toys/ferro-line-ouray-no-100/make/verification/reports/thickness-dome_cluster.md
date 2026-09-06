# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_dome_cluster.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-dome_cluster.md`

artifacts/make/r0001/product/cad-project/part_dome_cluster.stl: 1.70 cm3 solid, grid 0.133 mm (188x90x87), 51748 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 51748 samples) |
| thickness distribution | PASS | median 10.87 mm, p95 12.67 mm, max 24.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.76 of 1.70 cm3 (45%) in 1 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
