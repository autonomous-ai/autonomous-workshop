# Thickness and hollow

`artifacts/make/r0001/product/frosting-aloft/part_base.stl --nozzle 0.4 --report artifacts/make/r0001/product/frosting-aloft/measure/thickness-base.md`

artifacts/make/r0001/product/frosting-aloft/part_base.stl: 16.45 cm3 solid, grid 0.140 mm (376x465x62), 325331 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 325331 samples) |
| thickness distribution | PASS | median 7.98 mm, p95 49.28 mm, max 64.75 mm |
| hollowable at 1.20 mm wall | WARN | 9.35 of 16.45 cm3 (57%) in 1 pocket(s) |
| filament that would save | PASS | 1.40 cm3, 1.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
