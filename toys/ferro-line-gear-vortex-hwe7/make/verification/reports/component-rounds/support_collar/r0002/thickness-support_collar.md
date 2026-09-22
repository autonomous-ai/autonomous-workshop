# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_support_collar.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/support_collar/r0002/thickness-support_collar.md`

part_support_collar.step.py: 2.76 cm3 solid, grid 0.133 mm (192x192x95), 115686 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 115686 samples) |
| thickness distribution | PASS | median 3.47 mm, p95 12.00 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.60 of 2.76 cm3 (22%) in 1 pocket(s) |
| filament that would save | PASS | 0.09 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
