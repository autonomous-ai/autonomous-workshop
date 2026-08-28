# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_comet_orbit.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-comet_orbit.md`

artifacts/make/r0002/product/cad/comet_heist/part_comet_orbit.stl: 3.92 cm3 solid, grid 0.133 mm (229x230x52), 113011 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 113011 samples) |
| thickness distribution | PASS | median 5.47 mm, p95 29.93 mm, max 30.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.84 of 3.92 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 0.28 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
