# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_board.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/board/r0003/thickness-board.md`

part_board.step.py: 321.97 cm3 solid, grid 0.371 mm (532x532x37), 357457 surface samples, thickness resolved to 0.186 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.19) | PASS | 0.0% of surface below (0 of 357457 samples) |
| thickness distribution | PASS | median 11.89 mm, p95 151.93 mm, max 203.19 mm |
| hollowable at 1.20 mm wall | WARN | 238.33 of 321.97 cm3 (74%) in 1 pocket(s) |
| filament that would save | PASS | 35.75 cm3, 44.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
