# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_fork_leg.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/fork_leg/r0001/thickness-fork_leg.md`

part_fork_leg.step.py: 1.31 cm3 solid, grid 0.133 mm (256x406x35), 68023 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (62 of 68023 samples); thinnest 0.20 mm at (47.2, -55.0, 2.8) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.10% of surface, budget 2%); 8 more within measurement error of the limit |
| thickness distribution | PASS | median 3.93 mm, p95 8.87 mm, max 53.27 mm |
| hollowable at 1.20 mm wall | WARN | 0.21 of 1.31 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (47.2, -55.0, 2.8) | 62 | 1.2 | 3.8 | 0.33 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
