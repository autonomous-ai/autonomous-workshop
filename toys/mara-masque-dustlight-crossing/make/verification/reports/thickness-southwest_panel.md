# Thickness and hollow

`artifacts/make/r0001/product/cad/part_southwest_panel.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-southwest_panel.md`

part_southwest_panel.step.py: 58.36 cm3 solid, grid 0.188 mm (516x676x31), 375935 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 375935 samples); 694 more within measurement error of the limit |
| thickness distribution | PASS | median 4.88 mm, p95 95.87 mm, max 125.89 mm |
| hollowable at 1.20 mm wall | WARN | 29.18 of 58.36 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 4.38 cm3, 5.4 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
