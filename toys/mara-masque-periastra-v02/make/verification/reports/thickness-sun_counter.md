# Thickness and hollow

`artifacts/make/r0001/product/cad/part_sun_counter.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-sun_counter.md`

part_sun_counter.step.py: 1.18 cm3 solid, grid 0.133 mm (125x125x57), 41641 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 41641 samples) |
| thickness distribution | PASS | median 6.93 mm, p95 16.00 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.36 of 1.18 cm3 (31%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
