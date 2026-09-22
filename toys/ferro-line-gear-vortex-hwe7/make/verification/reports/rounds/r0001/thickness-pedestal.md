# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-pedestal.md`

part_pedestal.step.py: 34.88 cm3 solid, grid 0.251 mm (422x422x60), 368595 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 368595 samples) |
| thickness distribution | PASS | median 2.89 mm, p95 13.83 mm, max 48.90 mm |
| hollowable at 1.20 mm wall | WARN | 4.97 of 34.88 cm3 (14%) in 5 pocket(s) |
| filament that would save | PASS | 0.75 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
