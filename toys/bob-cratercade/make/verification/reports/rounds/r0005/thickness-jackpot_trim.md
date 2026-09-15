# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_trim.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-jackpot_trim.md`

part_jackpot_trim.step.py: 1.23 cm3 solid, grid 0.133 mm (95x95x80), 46136 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 46136 samples) |
| thickness distribution | PASS | median 9.53 mm, p95 12.00 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.37 of 1.23 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
