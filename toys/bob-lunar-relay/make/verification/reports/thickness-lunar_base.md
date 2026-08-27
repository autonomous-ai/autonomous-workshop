# Thickness and hollow

`artifacts/make/r0001/product/cad/moon_relay/part_lunar_base.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moon_relay/measure/thickness-lunar_base.md`

artifacts/make/r0001/product/cad/moon_relay/part_lunar_base.stl: 24.92 cm3 solid, grid 0.228 mm (408x242x114), 283465 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 283465 samples) |
| thickness distribution | PASS | median 3.88 mm, p95 54.05 mm, max 91.90 mm |
| hollowable at 1.20 mm wall | WARN | 9.35 of 24.92 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 1.40 cm3, 1.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
