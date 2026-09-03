# Thickness and hollow

`artifacts/make/r0001/product/cad/part_kickstand.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-kickstand.md`

artifacts/make/r0001/product/cad/part_kickstand.stl: 8.57 cm3 solid, grid 0.179 mm (609x492x38), 193551 surface samples, thickness resolved to 0.089 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 193551 samples) |
| thickness distribution | PASS | median 4.47 mm, p95 11.17 mm, max 87.02 mm |
| hollowable at 1.20 mm wall | WARN | 2.52 of 8.57 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.38 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
