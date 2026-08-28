# Thickness and hollow

`project/part_sector_rotor.stl --nozzle 0.4 --report project/measure/thickness-sector_rotor.md`

project/part_sector_rotor.stl: 3.51 cm3 solid, grid 0.133 mm (529x529x14), 353760 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 353760 samples) |
| thickness distribution | PASS | median 1.20 mm, p95 3.47 mm, max 65.07 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 3.51 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
