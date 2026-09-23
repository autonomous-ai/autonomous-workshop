# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mouth_back.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/mouth_back/r0004/thickness-mouth_back.md`

part_mouth_back.step.py: 24.63 cm3 solid, grid 0.147 mm (475x353x70), 375961 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 375961 samples) |
| thickness distribution | PASS | median 9.55 mm, p95 69.09 mm, max 69.09 mm |
| hollowable at 1.20 mm wall | WARN | 15.70 of 24.63 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.36 cm3, 2.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
