# Thickness and hollow

`part_torso.step.py --nozzle 0.4 --min-wall 1.1 --report /home/loginuserxx/harnesses/worktrees/autonomous-workshop/noble-lagoon-2/toys-spec/racer-mecha/build-a-toy/r00/detect/thickness19/thickness-torso.md`

part_torso.step.py: 116.99 cm3 solid, grid 0.284 mm (219x163x332), 288383 surface samples, thickness resolved to 0.142 mm

| check | status | detail |
|---|---|---|
| wall >= 1.10 mm (+/-0.14) | PASS | 0.0% of surface below (0 of 288383 samples); 164 more within measurement error of the limit |
| thickness distribution | PASS | median 24.46 mm, p95 81.06 mm, max 93.00 mm |
| hollowable at 1.20 mm wall | WARN | 89.04 of 116.99 cm3 (76%) in 1 pocket(s) |
| filament that would save | PASS | 13.36 cm3, 16.6 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
