# Thickness and hollow

`artifacts/make/r0001/product/cad/part_rear_shell.stl --nozzle 0.4 --voxel 0.16 --report artifacts/make/r0001/product/cad/measure/thickness-rear_shell-fine.md`

artifacts/make/r0001/product/cad/part_rear_shell.stl: 20.64 cm3 solid, grid 0.236 mm (483x525x42), 364855 surface samples, thickness resolved to 0.118 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | FAIL | 0.0% of surface below (5 of 364855 samples); thinnest 0.12 mm at (-48.5, -36.6, 2.4) in 3 region(s); 109 more within measurement error of the limit |
| thickness distribution | PASS | median 2.36 mm, p95 16.19 mm, max 120.09 mm |
| hollowable at 1.20 mm wall | WARN | 0.10 of 20.64 cm3 (0%) in 7 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

| # | thinnest | at | samples | area mm2 | runs mm |
|---|---|---|---|---|---|
| 1 | 0.12 mm | (-48.5, -36.6, 2.4) | 3 | 0.1 | 1.3 |
| 2 | 0.59 mm | (21.6, 35.7, 2.4) | 1 | 0.1 | 0.0 |
| 3 | 0.59 mm | (48.5, -35.9, 1.6) | 1 | 0.1 | 0.0 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
