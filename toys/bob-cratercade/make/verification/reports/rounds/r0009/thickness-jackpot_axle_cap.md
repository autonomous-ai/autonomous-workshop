# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_axle_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-jackpot_axle_cap.md`

part_jackpot_axle_cap.step.py: 3.74 cm3 solid, grid 0.133 mm (275x245x45), 158974 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 158974 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 32.00 mm, max 36.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.67 of 3.74 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
