# Thickness and hollow

`artifacts/make/r0001/product/cad/part_rear_shell.stl --nozzle 0.4 --voxel 0.16 --report work/playtest/r0001/replay/thickness-rear-shell-fine.md`

artifacts/make/r0001/product/cad/part_rear_shell.stl: 24.24 cm3 solid, grid 0.261 mm (438x477x54), 329831 surface samples, thickness resolved to 0.130 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.0% of surface below (2 of 329831 samples); thinnest 0.13 mm at (37.7, 38.6, 2.4) in 2 region(s); 2395 more within measurement error of the limit |
| thickness distribution | PASS | median 2.35 mm, p95 15.12 mm, max 120.15 mm |
| hollowable at 1.20 mm wall | WARN | 0.36 of 24.24 cm3 (1%) in 6 pocket(s), 4 too small to shell |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

| # | thinnest | at | samples | area mm2 | runs mm |
|---|---|---|---|---|---|
| 1 | 0.39 mm | (32.0, 43.4, 2.4) | 1 | 0.1 | 0.0 |
| 2 | 0.13 mm | (37.7, 38.6, 2.4) | 1 | 0.1 | 0.0 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
