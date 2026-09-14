# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/rounds/r0001/thickness-rind.md`

part_rind.step.py: 123.50 cm3 solid, grid 0.264 mm (535x497x43), 382431 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 382431 samples) |
| thickness distribution | PASS | median 7.92 mm, p95 136.48 mm, max 151.00 mm |
| hollowable at 1.20 mm wall | WARN | 74.80 of 123.50 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 11.22 cm3, 13.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
