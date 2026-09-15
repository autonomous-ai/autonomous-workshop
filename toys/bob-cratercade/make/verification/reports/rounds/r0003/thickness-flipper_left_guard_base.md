# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_left_guard_base.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-flipper_left_guard_base.md`

part_flipper_left_guard_base.step.py: 12.02 cm3 solid, grid 0.239 mm (495x278x87), 159369 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 159369 samples) |
| thickness distribution | PASS | median 2.87 mm, p95 24.90 mm, max 117.09 mm |
| hollowable at 1.20 mm wall | WARN | 2.10 of 12.02 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.31 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
