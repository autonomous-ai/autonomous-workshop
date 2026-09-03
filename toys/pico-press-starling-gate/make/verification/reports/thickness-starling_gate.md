# Thickness and hollow

`artifacts/make/r0001/product/cad/starling_gate.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-starling_gate.md`

artifacts/make/r0001/product/cad/starling_gate.stl: 110.11 cm3 solid, grid 0.239 mm (347x406x80), 366717 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 366717 samples) |
| thickness distribution | PASS | median 17.96 mm, p95 81.89 mm, max 90.39 mm |
| hollowable at 1.20 mm wall | WARN | 85.99 of 110.11 cm3 (78%) in 1 pocket(s) |
| filament that would save | PASS | 12.90 cm3, 16.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
