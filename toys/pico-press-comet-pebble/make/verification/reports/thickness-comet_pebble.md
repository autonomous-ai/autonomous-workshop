# Thickness and hollow

`artifacts/make/r0001/product/cad/comet_pebble.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-comet_pebble.md`

artifacts/make/r0001/product/cad/comet_pebble.stl: 41.77 cm3 solid, grid 0.217 mm (318x209x161), 147544 surface samples, thickness resolved to 0.109 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 147544 samples) |
| thickness distribution | PASS | median 32.80 mm, p95 39.20 mm, max 67.00 mm |
| hollowable at 1.20 mm wall | WARN | 33.73 of 41.77 cm3 (81%) in 1 pocket(s) |
| filament that would save | PASS | 5.06 cm3, 6.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
