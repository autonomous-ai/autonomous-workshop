# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_horn_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0002/thickness-horn_right.md`

part_horn_right.step.py: 1.11 cm3 solid, grid 0.133 mm (87x102x192), 33814 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 33814 samples) |
| thickness distribution | PASS | median 10.27 mm, p95 12.67 mm, max 22.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.51 of 1.11 cm3 (46%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
