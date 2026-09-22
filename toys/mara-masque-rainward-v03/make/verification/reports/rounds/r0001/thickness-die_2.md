# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_die_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-die_2.md`

part_die_2.step.py: 4.07 cm3 solid, grid 0.133 mm (125x125x125), 86668 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 86668 samples) |
| thickness distribution | PASS | median 15.93 mm, p95 16.00 mm, max 21.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.43 of 4.07 cm3 (60%) in 1 pocket(s) |
| filament that would save | PASS | 0.36 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
