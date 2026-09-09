# Thickness and hollow

`artifacts/make/r0001/product/cad/part_bill.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-bill.md`

artifacts/make/r0001/product/cad/part_bill.stl: 6.14 cm3 solid, grid 0.133 mm (492x202x48), 188288 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (0 of 188288 samples) |
| thickness distribution | PASS | median 5.73 mm, p95 23.73 mm, max 64.73 mm |
| hollowable at 1.20 mm wall | WARN | 2.54 of 6.14 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 0.38 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
