# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_orange_disc.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-orange_disc.md`

part_orange_disc.step.py: 1.98 cm3 solid, grid 0.133 mm (417x417x12), 244878 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 244878 samples) |
| thickness distribution | PASS | median 0.93 mm, p95 0.93 mm, max 19.20 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.98 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
