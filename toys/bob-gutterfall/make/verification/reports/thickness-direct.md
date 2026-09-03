# Thickness and hollow

`direct.stl --nozzle 0.4 --report measure/thickness-direct.md`

direct.stl: 139.10 cm3 solid, grid 0.430 mm (265x235x172), 158908 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | FAIL | 0.9% of surface below (1415 of 158908 samples); thinnest 0.22 mm at (-32.3, 15.3, 29.2) in 10 region(s); 612 more within measurement error of the limit |
| thickness distribution | PASS | median 16.77 mm, p95 55.69 mm, max 98.90 mm |
| hollowable at 1.20 mm wall | WARN | 107.19 of 139.10 cm3 (77%) in 1 pocket(s) |
| filament that would save | PASS | 16.08 cm3, 19.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

| # | thinnest | at | samples | area mm2 | runs mm |
|---|---|---|---|---|---|
| 1 | 0.22 mm | (-41.1, 15.5, 25.3) | 338 | 62.2 | 17.2 |
| 2 | 0.22 mm | (-41.7, -15.3, 21.6) | 278 | 51.2 | 17.2 |
| 3 | 0.22 mm | (-32.7, -15.4, 27.9) | 299 | 44.5 | 17.5 |
| 4 | 0.22 mm | (-32.3, 15.3, 29.2) | 265 | 39.4 | 17.3 |
| 5 | 0.22 mm | (-18.6, -15.3, 42.0) | 115 | 18.0 | 10.3 |
| 6 | 0.22 mm | (-18.0, 15.4, 42.1) | 112 | 17.1 | 9.7 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
