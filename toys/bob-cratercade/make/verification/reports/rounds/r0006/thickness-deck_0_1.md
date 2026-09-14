# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_1.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-deck_0_1.md`

part_deck_0_1.step.py: 162.27 cm3 solid, grid 0.337 mm (479x479x46), 374864 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (0 of 374864 samples) |
| thickness distribution | PASS | median 5.90 mm, p95 80.36 mm, max 203.50 mm |
| hollowable at 1.20 mm wall | WARN | 80.39 of 162.27 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 12.06 cm3, 15.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
