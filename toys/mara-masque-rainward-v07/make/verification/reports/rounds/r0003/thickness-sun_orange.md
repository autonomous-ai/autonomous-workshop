# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-sun_orange.md`

part_sun_orange.step.py: 91.77 cm3 solid, grid 0.291 mm (655x634x26), 358890 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (167 of 358890 samples); thinnest 0.29 mm at (-60.2, 52.2, 5.3) in 68 region(s); no region is a wall, 60 taper(s) at feature edges and 8 spot(s) too small to be a wall (0.02% of surface, budget 2%); 187 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.93 mm, max 184.23 mm |
| hollowable at 1.20 mm wall | WARN | 34.97 of 91.77 cm3 (38%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 5.25 cm3, 6.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (-28.1, 11.2, 5.4) | 5 | 0.7 | 4.4 | 0.16 |
| 2 | taper | 0.58 mm | (10.5, 26.2, 5.4) | 5 | 0.7 | 1.8 | 0.38 |
| 3 | taper | 0.44 mm | (-22.5, -17.7, 5.4) | 4 | 0.5 | 1.8 | 0.29 |
| 4 | spot | 0.58 mm | (-9.9, -79.1, 5.3) | 1 | 0.5 | 0.0 | 1.80 |
| 5 | spot | 0.44 mm | (-41.2, 68.3, 5.1) | 3 | 0.5 | 0.3 | 1.56 |
| 6 | spot | 0.29 mm | (-60.2, 52.2, 5.3) | 1 | 0.5 | 0.0 | 1.71 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
