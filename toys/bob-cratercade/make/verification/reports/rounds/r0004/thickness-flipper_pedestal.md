# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_pedestal.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-flipper_pedestal.md`

part_flipper_pedestal.step.py: 0.95 cm3 solid, grid 0.133 mm (140x140x35), 40855 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 40855 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 6.80 mm, max 6.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.24 of 0.95 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
