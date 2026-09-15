# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_receiver.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-access_receiver.md`

part_access_receiver.step.py: 70.96 cm3 solid, grid 0.430 mm (442x339x77), 165860 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | PASS | 0.0% of surface below (0 of 165860 samples); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 7.31 mm, p95 32.04 mm, max 159.96 mm |
| hollowable at 1.20 mm wall | WARN | 32.31 of 70.96 cm3 (46%) in 1 pocket(s) |
| filament that would save | PASS | 4.85 cm3, 6.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
