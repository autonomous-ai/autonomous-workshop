# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_tray_b.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-tray_b.md`

artifacts/make/r0002/product/cad/comet_heist/part_tray_b.stl: 125.99 cm3 solid, grid 0.430 mm (484x437x51), 399033 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | PASS | 0.0% of surface below (0 of 399033 samples) |
| thickness distribution | PASS | median 2.15 mm, p95 19.78 mm, max 205.98 mm |
| hollowable at 1.20 mm wall | WARN | 4.58 of 125.99 cm3 (4%) in 11 pocket(s) |
| filament that would save | PASS | 0.69 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
