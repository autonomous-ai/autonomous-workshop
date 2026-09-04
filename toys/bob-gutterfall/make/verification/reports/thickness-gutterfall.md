# Thickness and hollow

`gutterfall.stl --nozzle 0.4 --report measure/thickness-gutterfall.md`

gutterfall.stl: 139.38 cm3 solid, grid 0.390 mm (294x226x168), 262252 surface samples, thickness resolved to 0.195 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (0 of 262252 samples) |
| thickness distribution | PASS | median 23.60 mm, p95 60.46 mm, max 114.48 mm |
| hollowable at 1.20 mm wall | WARN | 110.15 of 139.38 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 16.52 cm3, 20.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
