# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_cab.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-cab.md`

artifacts/make/r0001/product/cad-project/part_cab.stl: 12.40 cm3 solid, grid 0.147 mm (202x216x243), 358022 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 358022 samples) |
| thickness distribution | PASS | median 2.50 mm, p95 30.94 mm, max 34.99 mm |
| hollowable at 1.20 mm wall | WARN | 4.16 of 12.40 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 0.62 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
