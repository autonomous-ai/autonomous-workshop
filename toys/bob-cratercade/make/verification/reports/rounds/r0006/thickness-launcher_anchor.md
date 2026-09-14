# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_anchor.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-launcher_anchor.md`

part_launcher_anchor.step.py: 1.81 cm3 solid, grid 0.133 mm (110x185x125), 72650 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 72650 samples) |
| thickness distribution | PASS | median 5.93 mm, p95 16.00 mm, max 24.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.53 of 1.81 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
