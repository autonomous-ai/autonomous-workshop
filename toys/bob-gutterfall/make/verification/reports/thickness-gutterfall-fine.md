# Thickness and hollow

`gutterfall.stl --nozzle 0.4 --voxel 0.3 --report measure/thickness-gutterfall-fine.md`

gutterfall.stl: 140.00 cm3 solid, grid 0.402 mm (283x220x184), 183442 surface samples, thickness resolved to 0.201 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | FAIL | 0.2% of surface below (380 of 183442 samples); thinnest 0.20 mm at (-21.0, -0.5, 17.0) in 16 region(s); 215 more within measurement error of the limit |
| thickness distribution | PASS | median 18.69 mm, p95 53.27 mm, max 94.28 mm |
| hollowable at 1.20 mm wall | WARN | 108.11 of 140.00 cm3 (77%) in 1 pocket(s) |
| filament that would save | PASS | 16.22 cm3, 20.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

| # | thinnest | at | samples | area mm2 | runs mm |
|---|---|---|---|---|---|
| 1 | 0.20 mm | (-35.8, -1.5, 46.6) | 167 | 21.8 | 37.4 |
| 2 | 0.20 mm | (-23.5, -8.0, 33.0) | 45 | 7.0 | 16.1 |
| 3 | 0.20 mm | (-52.7, 3.2, 24.7) | 36 | 4.4 | 13.2 |
| 4 | 0.20 mm | (21.1, -1.6, 30.7) | 72 | 3.6 | 11.9 |
| 5 | 0.20 mm | (-52.2, -5.0, 28.6) | 11 | 1.8 | 3.6 |
| 6 | 0.20 mm | (7.0, 2.5, 21.4) | 11 | 1.5 | 6.7 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
