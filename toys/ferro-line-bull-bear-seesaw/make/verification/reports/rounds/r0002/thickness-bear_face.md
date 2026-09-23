# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_face.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-bear_face.md`

part_bear_face.step.py: 0.86 cm3 solid, grid 0.133 mm (155x101x50), 40840 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 40840 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 19.93 mm, max 20.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.86 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
