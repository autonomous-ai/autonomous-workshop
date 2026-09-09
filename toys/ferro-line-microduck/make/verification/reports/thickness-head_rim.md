# Thickness and hollow

`artifacts/make/r0001/product/cad/part_head_rim.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-head_rim.md`

artifacts/make/r0001/product/cad/part_head_rim.stl: 1.09 cm3 solid, grid 0.133 mm (458x290x26), 70041 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 70041 samples); 2 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 2.80 mm, p95 4.20 mm, max 25.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.06 of 1.09 cm3 (5%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
