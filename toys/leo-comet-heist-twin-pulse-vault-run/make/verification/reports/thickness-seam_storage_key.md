# Thickness and hollow

`artifacts/make/r0002/product/cad/comet_heist/part_seam_storage_key.stl --nozzle 0.4 --report artifacts/make/r0002/product/cad/comet_heist/measure/thickness-seam_storage_key.md`

artifacts/make/r0002/product/cad/comet_heist/part_seam_storage_key.stl: 2.32 cm3 solid, grid 0.133 mm (395x95x35), 97279 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 97279 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 12.00 mm, max 52.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.65 of 2.32 cm3 (28%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
