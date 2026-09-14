# Thickness and hollow

`part_access_frame.step.py --nozzle 0.4 --report measure/thickness-access_frame.md`

part_access_frame.step.py: 53.93 cm3 solid, grid 0.410 mm (441x356x75), 144249 surface samples, thickness resolved to 0.205 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (0 of 144249 samples); 4 more within measurement error of the limit |
| thickness distribution | PASS | median 7.37 mm, p95 27.03 mm, max 159.72 mm |
| hollowable at 1.20 mm wall | WARN | 25.95 of 53.93 cm3 (48%) in 3 pocket(s), 4 too small to shell |
| filament that would save | PASS | 3.89 cm3, 4.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
