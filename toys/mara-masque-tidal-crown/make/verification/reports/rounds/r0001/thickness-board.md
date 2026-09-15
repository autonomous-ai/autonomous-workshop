# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_board.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-board.md`

part_board.step.py: 325.56 cm3 solid, grid 0.371 mm (532x532x37), 362752 surface samples, thickness resolved to 0.186 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.19) | PASS | 0.0% of surface below (0 of 362752 samples) |
| thickness distribution | PASS | median 11.89 mm, p95 151.93 mm, max 203.19 mm |
| hollowable at 1.20 mm wall | WARN | 243.95 of 325.56 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 36.59 cm3, 45.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
