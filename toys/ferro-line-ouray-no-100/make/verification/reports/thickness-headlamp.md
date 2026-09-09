# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_headlamp.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-headlamp.md`

artifacts/make/r0001/product/cad-project/part_headlamp.stl: 2.11 cm3 solid, grid 0.133 mm (100x115x96), 53780 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 53780 samples) |
| thickness distribution | PASS | median 12.13 mm, p95 14.60 mm, max 14.67 mm |
| hollowable at 1.20 mm wall | WARN | 1.09 of 2.11 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
