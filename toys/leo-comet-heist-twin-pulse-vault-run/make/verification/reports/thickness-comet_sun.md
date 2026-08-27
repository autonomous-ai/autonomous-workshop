# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_comet_sun.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-comet_sun.md`

artifacts/make/r0002/product/cad/comet_heist/part_comet_sun.stl: 4.07 cm3 solid, grid 0.133 mm (229x230x52), 111300 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 111300 samples) |
| thickness distribution | PASS | median 6.27 mm, p95 29.93 mm, max 30.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.01 of 4.07 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 0.30 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
