# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_apron_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-apron_right.md`

part_apron_right.step.py: 47.53 cm3 solid, grid 0.291 mm (504x225x103), 250787 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (0 of 250787 samples) |
| thickness distribution | PASS | median 4.66 mm, p95 28.52 mm, max 147.27 mm |
| hollowable at 1.20 mm wall | WARN | 22.58 of 47.53 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 3.39 cm3, 4.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
