# Thickness and hollow

`artifacts/make/r0001/product/cad/ember_knock.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-ember_knock.md`

artifacts/make/r0001/product/cad/ember_knock.stl: 48.27 cm3 solid, grid 0.251 mm (335x132x243), 229069 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 229069 samples) |
| thickness distribution | PASS | median 12.45 mm, p95 41.99 mm, max 80.96 mm |
| hollowable at 1.20 mm wall | WARN | 31.91 of 48.27 cm3 (66%) in 1 pocket(s) |
| filament that would save | PASS | 4.79 cm3, 5.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
