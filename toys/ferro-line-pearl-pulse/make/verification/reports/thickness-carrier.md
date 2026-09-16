# Thickness and hollow

`artifacts/make/r0001/product/cad/part_carrier.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-carrier.md`

part_carrier.step.py: 2.19 cm3 solid, grid 0.133 mm (437x325x73), 127561 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 127561 samples) |
| thickness distribution | PASS | median 3.33 mm, p95 9.07 mm, max 25.67 mm |
| hollowable at 1.20 mm wall | WARN | 0.24 of 2.19 cm3 (11%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
