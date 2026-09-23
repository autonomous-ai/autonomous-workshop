# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mount_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/mount_pin/r0001/thickness-mount_pin.md`

part_mount_pin.step.py: 0.59 cm3 solid, grid 0.133 mm (80x80x141), 31053 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.1% of surface below (643 of 31053 samples); thinnest 0.13 mm at (1.5, -2.6, 15.0) in 4 region(s); 4 wall(s) (widest band 1.13 mm); 104 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 13.33 mm, max 18.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.11 of 0.59 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (1.5, 2.6, 13.7) | 174 | 3.3 | 2.9 | 1.13 |
| 2 | wall | 0.13 mm | (1.5, -2.6, 15.0) | 165 | 3.2 | 2.9 | 1.10 |
| 3 | wall | 0.13 mm | (-1.4, -2.6, 15.6) | 155 | 3.0 | 2.9 | 1.02 |
| 4 | wall | 0.13 mm | (-1.5, 2.6, 14.5) | 149 | 2.9 | 2.8 | 1.03 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
