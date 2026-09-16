# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_chain.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/chain/r0001/thickness-chain.md`

part_chain.step.py: 1.63 cm3 solid, grid 0.133 mm (94x616x63), 147784 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.8% of surface below (2613 of 147784 samples); thinnest 0.13 mm at (1.9, -34.9, 2.0) in 37 region(s); no region is a wall, 37 taper(s) at feature edges (1.79% of surface, budget 2%); 161 more within measurement error of the limit |
| thickness distribution | PASS | median 1.60 mm, p95 5.53 mm, max 18.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 1.63 cm3 (1%) in 1 pocket(s), 8 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-2.2, -17.1, 7.7) | 260 | 4.6 | 6.7 | 0.69 |
| 2 | taper | 0.33 mm | (2.0, -45.5, 7.7) | 255 | 4.6 | 6.7 | 0.68 |
| 3 | taper | 0.33 mm | (2.8, -40.0, 7.7) | 253 | 4.5 | 6.7 | 0.67 |
| 4 | taper | 0.33 mm | (2.3, -31.7, 7.7) | 242 | 4.3 | 6.7 | 0.65 |
| 5 | taper | 0.33 mm | (2.8, -24.6, 7.7) | 241 | 4.3 | 6.7 | 0.64 |
| 6 | taper | 0.33 mm | (1.2, -70.5, 7.7) | 228 | 4.1 | 6.6 | 0.62 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
