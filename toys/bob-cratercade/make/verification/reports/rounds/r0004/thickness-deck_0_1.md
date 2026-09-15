# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_1.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-deck_0_1.md`

part_deck_0_1.step.py: 162.19 cm3 solid, grid 0.337 mm (479x479x46), 375408 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 375408 samples) |
| thickness distribution | PASS | median 5.90 mm, p95 79.51 mm, max 203.50 mm |
| hollowable at 1.20 mm wall | WARN | 80.36 of 162.19 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 12.05 cm3, 14.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
