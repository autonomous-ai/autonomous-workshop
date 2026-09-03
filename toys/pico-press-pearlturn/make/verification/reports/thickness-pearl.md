# Thickness and hollow

`artifacts/make/r0001/product/pearlturn/part_pearl.stl --nozzle 0.4 --report artifacts/make/r0001/product/pearlturn/measure/thickness-pearl.md`

artifacts/make/r0001/product/pearlturn/part_pearl.stl: 9.86 cm3 solid, grid 0.133 mm (185x185x170), 139792 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 139792 samples) |
| thickness distribution | PASS | median 23.93 mm, p95 26.33 mm, max 31.33 mm |
| hollowable at 1.20 mm wall | WARN | 7.10 of 9.86 cm3 (72%) in 1 pocket(s) |
| filament that would save | PASS | 1.06 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
