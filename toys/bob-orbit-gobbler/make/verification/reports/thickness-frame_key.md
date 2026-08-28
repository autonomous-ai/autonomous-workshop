# Thickness and hollow

`cad/part_frame_key.stl --nozzle 0.4 --report cad/measure/thickness-frame_key.md`

cad/part_frame_key.stl: 0.36 cm3 solid, grid 0.133 mm (57x110x33), 19656 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 19656 samples) |
| thickness distribution | PASS | median 3.73 mm, p95 14.00 mm, max 14.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.36 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
