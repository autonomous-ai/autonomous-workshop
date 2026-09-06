# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_diamond_stack.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-diamond_stack.md`

artifacts/make/r0001/product/cad-project/part_diamond_stack.stl: 1.65 cm3 solid, grid 0.133 mm (140x140x111), 49109 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 49109 samples) |
| thickness distribution | PASS | median 9.73 mm, p95 17.93 mm, max 18.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.74 of 1.65 cm3 (45%) in 1 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
