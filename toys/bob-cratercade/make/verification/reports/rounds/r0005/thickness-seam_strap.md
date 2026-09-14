# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_seam_strap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-seam_strap.md`

part_seam_strap.step.py: 17.64 cm3 solid, grid 0.154 mm (212x782x63), 329032 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 329032 samples) |
| thickness distribution | PASS | median 6.02 mm, p95 26.01 mm, max 119.93 mm |
| hollowable at 1.20 mm wall | WARN | 8.73 of 17.64 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 1.31 cm3, 1.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
