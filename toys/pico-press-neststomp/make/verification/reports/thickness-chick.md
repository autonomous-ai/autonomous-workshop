# Thickness and hollow

`artifacts/make/r0001/product/neststomp/part_chick.stl --nozzle 0.4 --report artifacts/make/r0001/product/neststomp/measure/thickness-chick.md`

artifacts/make/r0001/product/neststomp/part_chick.stl: 19.71 cm3 solid, grid 0.133 mm (275x252x173), 240355 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 240355 samples) |
| thickness distribution | PASS | median 30.40 mm, p95 35.20 mm, max 35.53 mm |
| hollowable at 1.20 mm wall | WARN | 14.90 of 19.71 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 2.24 cm3, 2.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
