# Thickness and hollow

`artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/pocket_eclipse/measure/thickness-pocket_eclipse.md`

artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.stl: 24.00 cm3 solid, grid 0.337 mm (267x171x236), 115187 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 115187 samples) |
| thickness distribution | PASS | median 4.04 mm, p95 51.55 mm, max 90.63 mm |
| hollowable at 1.20 mm wall | WARN | 8.40 of 24.00 cm3 (35%) in 1 pocket(s) |
| filament that would save | PASS | 1.26 cm3, 1.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
