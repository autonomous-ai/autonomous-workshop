# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_moon_counter.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-moon_counter.md`

part_moon_counter.step.py: 1.21 cm3 solid, grid 0.133 mm (125x125x57), 38714 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 38714 samples) |
| thickness distribution | PASS | median 6.93 mm, p95 16.00 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.46 of 1.21 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
