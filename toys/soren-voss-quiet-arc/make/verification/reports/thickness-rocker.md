# Thickness and hollow

`project/part_rocker.stl --nozzle 0.4 --report project/measure/thickness-rocker.md`

project/part_rocker.stl: 31.22 cm3 solid, grid 0.162 mm (428x140x178), 245903 surface samples, thickness resolved to 0.081 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 245903 samples) |
| thickness distribution | PASS | median 21.31 mm, p95 28.04 mm, max 68.07 mm |
| hollowable at 1.20 mm wall | WARN | 24.07 of 31.22 cm3 (77%) in 1 pocket(s) |
| filament that would save | PASS | 3.61 cm3, 4.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
