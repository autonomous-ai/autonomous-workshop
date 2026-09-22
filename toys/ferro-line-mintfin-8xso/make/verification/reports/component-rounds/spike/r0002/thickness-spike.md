# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_spike.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/spike/r0002/thickness-spike.md`

part_spike.step.py: 0.30 cm3 solid, grid 0.133 mm (65x65x95), 14429 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 14429 samples) |
| thickness distribution | PASS | median 6.73 mm, p95 8.40 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 0.30 cm3 (26%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
