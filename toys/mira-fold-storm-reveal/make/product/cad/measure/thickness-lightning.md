# Thickness and hollow

`project/part_lightning.stl --nozzle 0.4 --report project/measure/thickness-lightning.md`

project/part_lightning.stl: 1.17 cm3 solid, grid 0.133 mm (354x155x56), 69346 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 69346 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 11.47 mm, max 41.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.11 of 1.17 cm3 (10%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
