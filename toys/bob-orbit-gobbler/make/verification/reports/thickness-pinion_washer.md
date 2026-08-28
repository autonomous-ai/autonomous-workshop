# Thickness and hollow

`cad/part_pinion_washer.stl --nozzle 0.4 --report cad/measure/thickness-pinion_washer.md`

cad/part_pinion_washer.stl: 0.23 cm3 solid, grid 0.133 mm (125x125x20), 22274 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 22274 samples) |
| thickness distribution | PASS | median 2.00 mm, p95 2.80 mm, max 2.87 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.23 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
