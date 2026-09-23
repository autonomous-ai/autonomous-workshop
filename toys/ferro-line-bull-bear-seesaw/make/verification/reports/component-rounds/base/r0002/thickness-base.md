# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_base.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/base/r0002/thickness-base.md`

part_base.step.py: 48.19 cm3 solid, grid 0.251 mm (442x283x84), 287252 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 287252 samples) |
| thickness distribution | PASS | median 6.03 mm, p95 69.89 mm, max 124.20 mm |
| hollowable at 1.20 mm wall | WARN | 26.21 of 48.19 cm3 (54%) in 1 pocket(s) |
| filament that would save | PASS | 3.93 cm3, 4.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
