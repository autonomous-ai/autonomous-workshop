# Thickness and hollow

`artifacts/make/r0001/product/cad/part_neck_skin.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-neck_skin.md`

artifacts/make/r0001/product/cad/part_neck_skin.stl: 1.49 cm3 solid, grid 0.133 mm (222x239x26), 82477 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 82477 samples); 1 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 2.80 mm, p95 18.27 mm, max 31.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.13 of 1.49 cm3 (9%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
