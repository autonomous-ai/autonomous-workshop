# Thickness and hollow

`part_flipper_right_guard_base.step.py --nozzle 0.4 --report measure/flipper-guard-repair/check_thickness-right_guard_base-final.md`

part_flipper_right_guard_base.step.py: 8.40 cm3 solid, grid 0.197 mm (398x272x104), 161864 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 161864 samples) |
| thickness distribution | PASS | median 2.95 mm, p95 24.43 mm, max 77.02 mm |
| hollowable at 1.20 mm wall | WARN | 1.77 of 8.40 cm3 (21%) in 1 pocket(s) |
| filament that would save | PASS | 0.26 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
