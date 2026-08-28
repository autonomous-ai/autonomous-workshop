# Thickness and hollow

`cad/part_follower_roller.stl --nozzle 0.4 --report cad/measure/thickness-follower_roller.md`

cad/part_follower_roller.stl: 0.11 cm3 solid, grid 0.133 mm (65x65x35), 12703 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 12703 samples) |
| thickness distribution | PASS | median 1.33 mm, p95 4.00 mm, max 4.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.11 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
