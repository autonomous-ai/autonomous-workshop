# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_face_highlight.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-face_highlight.md`

part_face_highlight.step.py: 0.01 cm3 solid, grid 0.200 mm (19x19x11), 567 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 567 samples); 153 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 2.80 mm, max 2.90 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.01 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
