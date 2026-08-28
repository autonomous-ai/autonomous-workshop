# Thickness and hollow

`cad/part_mouth_bezel.stl --nozzle 0.4 --report cad/measure/thickness-mouth_bezel.md`

cad/part_mouth_bezel.stl: 13.13 cm3 solid, grid 0.277 mm (328x335x103), 128046 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 128046 samples) |
| thickness distribution | PASS | median 3.05 mm, p95 32.02 mm, max 77.89 mm |
| hollowable at 1.20 mm wall | WARN | 3.37 of 13.13 cm3 (26%) in 1 pocket(s) |
| filament that would save | PASS | 0.51 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
