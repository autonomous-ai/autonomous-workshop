# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal_lid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-pedestal_lid.md`

part_pedestal_lid.step.py: 27.05 cm3 solid, grid 0.207 mm (488x481x46), 387601 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (1 of 387601 samples); thinnest 0.62 mm at (-24.7, 42.6, 8.5) in 1 region(s); no region is a wall, 0 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 2.90 mm, p95 8.48 mm, max 98.46 mm |
| hollowable at 1.20 mm wall | WARN | 4.03 of 27.05 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.60 cm3, 0.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.62 mm | (-24.7, 42.6, 8.5) | 1 | 0.2 | 0.0 | 1.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
