# Thickness and hollow

`project/part_rainbow.stl --nozzle 0.4 --report project/measure/thickness-rainbow.md`

project/part_rainbow.stl: 1.59 cm3 solid, grid 0.133 mm (140x372x87), 85951 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 85951 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 17.00 mm, max 25.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 1.59 cm3 (14%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
