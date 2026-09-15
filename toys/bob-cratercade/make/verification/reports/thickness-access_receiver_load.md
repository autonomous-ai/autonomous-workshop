# Thickness and hollow

`part_access_receiver_load.step.py --nozzle 0.4 --report measure/thickness-access_receiver_load.md`

part_access_receiver_load.step.py: 70.84 cm3 solid, grid 0.430 mm (442x339x77), 165783 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | PASS | 0.0% of surface below (0 of 165783 samples) |
| thickness distribution | PASS | median 7.31 mm, p95 31.61 mm, max 159.53 mm |
| hollowable at 1.20 mm wall | WARN | 32.25 of 70.84 cm3 (46%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 4.84 cm3, 6.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
