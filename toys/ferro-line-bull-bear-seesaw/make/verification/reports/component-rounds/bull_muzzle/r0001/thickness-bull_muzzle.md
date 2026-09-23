# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_muzzle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_muzzle/r0001/thickness-bull_muzzle.md`

part_bull_muzzle.step.py: 2.05 cm3 solid, grid 0.133 mm (290x200x60), 101942 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.0% of surface below (2062 of 101942 samples); thinnest 0.47 mm at (-12.1, 9.8, 3.6) in 1 region(s); 1 wall(s) (widest band 0.86 mm); 304 more within measurement error of the limit |
| thickness distribution | PASS | median 3.53 mm, p95 9.27 mm, max 37.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.33 of 2.05 cm3 (16%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.47 mm | (-12.1, 9.8, 3.6) | 2062 | 39.6 | 45.8 | 0.86 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
