# Thickness and hollow

`artifacts/make/r0001/product/cad/moon_relay/part_moon_rocker.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moon_relay/measure/thickness-moon_rocker.md`

artifacts/make/r0001/product/cad/moon_relay/part_moon_rocker.stl: 17.32 cm3 solid, grid 0.133 mm (620x170x110), 329028 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 329028 samples) |
| thickness distribution | PASS | median 14.00 mm, p95 32.27 mm, max 81.67 mm |
| hollowable at 1.20 mm wall | WARN | 10.90 of 17.32 cm3 (63%) in 2 pocket(s) |
| filament that would save | PASS | 1.64 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
