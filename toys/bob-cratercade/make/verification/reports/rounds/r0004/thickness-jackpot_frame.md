# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-jackpot_frame.md`

part_jackpot_frame.step.py: 30.06 cm3 solid, grid 0.321 mm (323x242x136), 146815 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (0 of 146815 samples) |
| thickness distribution | PASS | median 5.13 mm, p95 33.69 mm, max 102.04 mm |
| hollowable at 1.20 mm wall | WARN | 12.47 of 30.06 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 1.87 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
