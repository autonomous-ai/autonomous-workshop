# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/carrier/r0002/thickness-carrier.md`

part_carrier.step.py: 10.41 cm3 solid, grid 0.140 mm (483x619x38), 355021 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 355021 samples) |
| thickness distribution | PASS | median 4.55 mm, p95 22.40 mm, max 62.09 mm |
| hollowable at 1.20 mm wall | WARN | 3.10 of 10.41 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.46 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
