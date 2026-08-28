# Thickness and hollow

`cad/part_pinion.stl --nozzle 0.4 --report cad/measure/thickness-pinion.md`

cad/part_pinion.stl: 4.12 cm3 solid, grid 0.133 mm (206x206x240), 138747 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 138747 samples) |
| thickness distribution | PASS | median 7.47 mm, p95 27.33 mm, max 31.33 mm |
| hollowable at 1.20 mm wall | WARN | 1.77 of 4.12 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.26 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
