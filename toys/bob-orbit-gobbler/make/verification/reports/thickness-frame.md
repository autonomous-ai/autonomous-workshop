# Thickness and hollow

`cad/part_frame.stl --nozzle 0.4 --report cad/measure/thickness-frame.md`

cad/part_frame.stl: 40.15 cm3 solid, grid 0.337 mm (563x580x35), 309917 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 309917 samples) |
| thickness distribution | PASS | median 4.04 mm, p95 8.09 mm, max 90.13 mm |
| hollowable at 1.20 mm wall | WARN | 6.05 of 40.15 cm3 (15%) in 4 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
