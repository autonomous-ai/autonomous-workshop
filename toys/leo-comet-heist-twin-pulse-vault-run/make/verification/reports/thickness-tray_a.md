# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_tray_a.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-tray_a.md`

artifacts/make/r0002/product/cad/comet_heist/part_tray_a.stl: 124.67 cm3 solid, grid 0.430 mm (484x437x51), 398923 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | PASS | 0.0% of surface below (0 of 398923 samples) |
| thickness distribution | PASS | median 2.15 mm, p95 19.78 mm, max 205.98 mm |
| hollowable at 1.20 mm wall | WARN | 3.28 of 124.67 cm3 (3%) in 9 pocket(s) |
| filament that would save | PASS | 0.49 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
