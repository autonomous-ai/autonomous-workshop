# Thickness and hollow

`artifacts/make/r0001/product/cad/moonwake/moonwake.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moonwake/measure/thickness-moonwake.md`

artifacts/make/r0001/product/cad/moonwake/moonwake.stl: 37.20 cm3 solid, grid 0.291 mm (328x142x238), 252008 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 252008 samples); 30 more within measurement error of the limit |
| thickness distribution | PASS | median 4.37 mm, p95 39.87 mm, max 94.01 mm |
| hollowable at 1.20 mm wall | WARN | 15.03 of 37.20 cm3 (40%) in 2 pocket(s) |
| filament that would save | PASS | 2.25 cm3, 2.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
