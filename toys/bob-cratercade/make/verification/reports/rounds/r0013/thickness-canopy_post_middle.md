# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_middle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0013/thickness-canopy_post_middle.md`

part_canopy_post_middle.step.py: 18.91 cm3 solid, grid 0.147 mm (107x127x808), 380828 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 380828 samples) |
| thickness distribution | PASS | median 3.97 mm, p95 17.93 mm, max 111.21 mm |
| hollowable at 1.20 mm wall | WARN | 5.58 of 18.91 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.84 cm3, 1.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
