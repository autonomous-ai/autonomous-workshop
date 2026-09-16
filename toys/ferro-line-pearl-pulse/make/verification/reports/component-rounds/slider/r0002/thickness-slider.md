# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_slider.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/slider/r0002/thickness-slider.md`

part_slider.step.py: 2.35 cm3 solid, grid 0.188 mm (273x280x151), 108928 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 108928 samples) |
| thickness distribution | PASS | median 1.13 mm, p95 5.44 mm, max 27.39 mm |
| hollowable at 1.20 mm wall | WARN | 0.05 of 2.35 cm3 (2%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
