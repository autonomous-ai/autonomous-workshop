# Thickness and hollow

`cad/part_lunar_slider.stl --nozzle 0.4 --report cad/measure/thickness-lunar_slider.md`

cad/part_lunar_slider.stl: 1.08 cm3 solid, grid 0.133 mm (260x95x29), 62265 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 62265 samples) |
| thickness distribution | PASS | median 3.20 mm, p95 13.79 mm, max 34.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 1.08 cm3 (14%) in 2 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
