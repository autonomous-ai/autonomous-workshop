# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-return_hood_2.md`

part_return_hood_2.step.py: 25.18 cm3 solid, grid 0.228 mm (224x486x110), 354929 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 354929 samples) |
| thickness distribution | PASS | median 3.19 mm, p95 25.88 mm, max 109.69 mm |
| hollowable at 1.20 mm wall | WARN | 5.69 of 25.18 cm3 (23%) in 1 pocket(s) |
| filament that would save | PASS | 0.85 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
