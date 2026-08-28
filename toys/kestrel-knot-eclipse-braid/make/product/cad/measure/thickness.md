# Thickness and hollow

`artifacts/make/r0001/product/assembled.stl --min-wall 0.8 --report artifacts/make/r0001/product/cad/measure/thickness.md`

artifacts/make/r0001/product/assembled.stl: 15.31 cm3 solid, grid 0.291 mm (403x293x94), 214751 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 214751 samples) |
| thickness distribution | PASS | median 2.62 mm, p95 6.99 mm, max 115.84 mm |
| hollowable at 1.20 mm wall | WARN | 1.42 of 15.31 cm3 (9%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.21 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
