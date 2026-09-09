# Thickness and hollow

`artifacts/make/r0001/product/cad/part_inner.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-inner.md`

artifacts/make/r0001/product/cad/part_inner.stl: 21.77 cm3 solid, grid 0.154 mm (549x549x37), 387009 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 387009 samples) |
| thickness distribution | PASS | median 4.94 mm, p95 83.81 mm, max 84.04 mm |
| hollowable at 1.20 mm wall | WARN | 6.21 of 21.77 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.93 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
