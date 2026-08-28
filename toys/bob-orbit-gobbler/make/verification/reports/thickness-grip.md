# Thickness and hollow

`cad/part_grip.stl --nozzle 0.4 --report cad/measure/thickness-grip.md`

cad/part_grip.stl: 2.16 cm3 solid, grid 0.133 mm (110x110x170), 98047 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 98047 samples) |
| thickness distribution | PASS | median 2.80 mm, p95 22.00 mm, max 22.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.21 of 2.16 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
