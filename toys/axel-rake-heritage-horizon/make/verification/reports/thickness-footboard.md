# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_footboard.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-footboard.md`

part_footboard.step.py: 0.60 cm3 solid, grid 0.133 mm (200x65x27), 30834 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 30834 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 25.93 mm, max 26.80 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.60 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
