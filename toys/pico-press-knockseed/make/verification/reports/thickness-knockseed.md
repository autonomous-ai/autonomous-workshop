# Thickness and hollow

`artifacts/make/r0001/product/cad/knockseed.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-knockseed.md`

artifacts/make/r0001/product/cad/knockseed.stl: 4.56 cm3 solid, grid 0.133 mm (275x143x100), 85620 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 85620 samples) |
| thickness distribution | PASS | median 13.47 mm, p95 18.07 mm, max 34.60 mm |
| hollowable at 1.20 mm wall | WARN | 2.91 of 4.56 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 0.44 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
