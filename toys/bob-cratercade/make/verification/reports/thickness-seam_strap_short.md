# Thickness and hollow

`part_seam_strap_short.step.py --nozzle 0.4 --report measure/thickness-seam_strap_short.md`

part_seam_strap_short.step.py: 11.81 cm3 solid, grid 0.133 mm (245x605x72), 309445 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 309445 samples) |
| thickness distribution | PASS | median 6.00 mm, p95 26.00 mm, max 80.00 mm |
| hollowable at 1.20 mm wall | WARN | 5.78 of 11.81 cm3 (49%) in 1 pocket(s) |
| filament that would save | PASS | 0.87 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
