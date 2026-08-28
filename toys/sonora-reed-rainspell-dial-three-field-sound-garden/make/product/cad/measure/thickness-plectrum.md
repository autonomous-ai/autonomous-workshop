# Thickness and hollow

`project/part_plectrum.stl --nozzle 0.4 --report project/measure/thickness-plectrum.md`

project/part_plectrum.stl: 6.48 cm3 solid, grid 0.133 mm (185x185x239), 134586 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 134586 samples) |
| thickness distribution | PASS | median 12.00 mm, p95 24.00 mm, max 32.07 mm |
| hollowable at 1.20 mm wall | WARN | 3.95 of 6.48 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.59 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
