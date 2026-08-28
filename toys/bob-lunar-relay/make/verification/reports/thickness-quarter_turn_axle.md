# Thickness and hollow

`artifacts/make/r0001/product/cad/moon_relay/part_quarter_turn_axle.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moon_relay/measure/thickness-quarter_turn_axle.md`

artifacts/make/r0001/product/cad/moon_relay/part_quarter_turn_axle.stl: 1.34 cm3 solid, grid 0.133 mm (102x102x273), 60731 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 60731 samples) |
| thickness distribution | PASS | median 5.93 mm, p95 30.47 mm, max 35.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.34 of 1.34 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
