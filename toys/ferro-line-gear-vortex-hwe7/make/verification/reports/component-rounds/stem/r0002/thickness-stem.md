# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_stem.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/stem/r0002/thickness-stem.md`

part_stem.step.py: 11.34 cm3 solid, grid 0.133 mm (95x95x811), 227292 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 227292 samples) |
| thickness distribution | PASS | median 11.93 mm, p95 15.20 mm, max 107.47 mm |
| hollowable at 1.20 mm wall | WARN | 6.87 of 11.34 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 1.03 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
