# Thickness and hollow

`part_jackpot_rocker.step.py --nozzle 0.4 --report measure/thickness-jackpot_rocker.md`

part_jackpot_rocker.step.py: 22.84 cm3 solid, grid 0.337 mm (223x324x165), 100160 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (36 of 100160 samples); thinnest 0.34 mm at (-12.6, 4.0, 17.6) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.04% of surface, budget 2%); 21 more within measurement error of the limit |
| thickness distribution | PASS | median 3.71 mm, p95 32.01 mm, max 74.63 mm |
| hollowable at 1.20 mm wall | WARN | 9.64 of 22.84 cm3 (42%) in 2 pocket(s) |
| filament that would save | PASS | 1.45 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (6.2, 4.0, 17.6) | 21 | 2.6 | 16.0 | 0.16 |
| 2 | taper | 0.34 mm | (-12.6, 4.0, 17.6) | 10 | 1.2 | 3.2 | 0.39 |
| 3 | taper | 0.51 mm | (11.2, 4.4, 17.8) | 4 | 0.5 | 2.2 | 0.22 |
| 4 | taper | 0.34 mm | (14.0, 4.0, 17.6) | 1 | 0.1 | 0.0 | 0.38 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
