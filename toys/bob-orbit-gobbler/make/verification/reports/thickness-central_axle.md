# Thickness and hollow

`cad/part_central_axle.stl --nozzle 0.4 --report cad/measure/thickness-central_axle.md`

cad/part_central_axle.stl: 2.54 cm3 solid, grid 0.133 mm (140x140x302), 91412 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 91412 samples) |
| thickness distribution | PASS | median 7.93 mm, p95 35.73 mm, max 39.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.93 of 2.54 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
