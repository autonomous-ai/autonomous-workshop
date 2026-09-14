# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_1_0.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-deck_1_0.md`

part_deck_1_0.step.py: 170.43 cm3 solid, grid 0.337 mm (479x479x46), 369890 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 369890 samples) |
| thickness distribution | PASS | median 5.90 mm, p95 62.50 mm, max 193.23 mm |
| hollowable at 1.20 mm wall | WARN | 82.18 of 170.43 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 12.33 cm3, 15.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
