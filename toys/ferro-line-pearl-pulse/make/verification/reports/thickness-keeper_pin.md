# Thickness and hollow

`artifacts/make/r0001/product/cad/part_keeper_pin.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-keeper_pin.md`

part_keeper_pin.step.py: 0.05 cm3 solid, grid 0.133 mm (35x35x78), 5499 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 5499 samples) |
| thickness distribution | PASS | median 2.33 mm, p95 6.80 mm, max 9.73 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.05 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
