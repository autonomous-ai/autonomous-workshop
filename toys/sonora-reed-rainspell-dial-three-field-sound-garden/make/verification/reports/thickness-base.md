# Thickness and hollow

`project/part_base.stl --nozzle 0.4 --report project/measure/thickness-base.md`

project/part_base.stl: 168.68 cm3 solid, grid 0.390 mm (312x312x112), 330224 surface samples, thickness resolved to 0.195 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (0 of 330224 samples) |
| thickness distribution | PASS | median 7.22 mm, p95 101.02 mm, max 119.74 mm |
| hollowable at 1.20 mm wall | WARN | 113.77 of 168.68 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 17.07 cm3, 21.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
