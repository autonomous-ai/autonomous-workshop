# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_rocker.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-jackpot_rocker.md`

part_jackpot_rocker.step.py: 24.59 cm3 solid, grid 0.337 mm (223x324x165), 114712 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (29 of 114712 samples); thinnest 0.34 mm at (-13.2, 4.0, 17.6) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.03% of surface, budget 2%); 28 more within measurement error of the limit |
| thickness distribution | PASS | median 3.54 mm, p95 32.01 mm, max 74.63 mm |
| hollowable at 1.20 mm wall | WARN | 9.64 of 24.59 cm3 (39%) in 2 pocket(s) |
| filament that would save | PASS | 1.45 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (-13.2, 4.0, 17.6) | 15 | 1.9 | 11.5 | 0.16 |
| 2 | taper | 0.34 mm | (6.7, 4.0, 17.6) | 8 | 1.0 | 6.4 | 0.16 |
| 3 | taper | 0.34 mm | (2.6, 4.0, 17.6) | 6 | 0.8 | 3.7 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
