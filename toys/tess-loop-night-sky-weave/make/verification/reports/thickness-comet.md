# Thickness and hollow

`_verification/make-r0001-7fbab280/project/part_comet.stl --nozzle 0.4 --report _verification/make-r0001-7fbab280/project/measure/thickness-comet.md`

_verification/make-r0001-7fbab280/project/part_comet.stl: 5.27 cm3 solid, grid 0.133 mm (241x241x47), 163043 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 163043 samples) |
| thickness distribution | PASS | median 5.60 mm, p95 31.47 mm, max 40.93 mm |
| hollowable at 1.20 mm wall | WARN | 2.22 of 5.27 cm3 (42%) in 1 pocket(s) |
| filament that would save | PASS | 0.33 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
