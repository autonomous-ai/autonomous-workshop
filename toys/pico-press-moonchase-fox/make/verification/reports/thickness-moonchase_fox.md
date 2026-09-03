# Thickness and hollow

`artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moonchase_fox/measure/thickness-moonchase_fox.md`

artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.stl: 110.98 cm3 solid, grid 0.251 mm (377x314x100), 312895 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 312895 samples) |
| thickness distribution | PASS | median 23.88 mm, p95 46.01 mm, max 80.83 mm |
| hollowable at 1.20 mm wall | WARN | 87.50 of 110.98 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 13.13 cm3, 16.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
