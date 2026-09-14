# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_bar_riser.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-bar_riser.md`

part_bar_riser.step.py: 0.37 cm3 solid, grid 0.133 mm (65x52x65), 16073 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 16073 samples) |
| thickness distribution | PASS | median 7.40 mm, p95 8.00 mm, max 8.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.11 of 0.37 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
