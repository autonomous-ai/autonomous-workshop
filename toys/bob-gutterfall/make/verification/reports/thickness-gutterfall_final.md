# Thickness and hollow

`artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/gutterfall/measure/thickness-gutterfall_final.md`

artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.stl: 138.99 cm3 solid, grid 0.390 mm (294x220x164), 183187 surface samples, thickness resolved to 0.195 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (0 of 183187 samples) |
| thickness distribution | PASS | median 18.92 mm, p95 57.14 mm, max 113.89 mm |
| hollowable at 1.20 mm wall | WARN | 109.04 of 138.99 cm3 (78%) in 1 pocket(s) |
| filament that would save | PASS | 16.36 cm3, 20.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
