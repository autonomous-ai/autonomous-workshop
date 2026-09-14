# Overhang and support

`artifacts/make/r0001/product/cad/part_white_bishop.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-white_bishop.md`

part_white_bishop.step.py: 15.5 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 13.0% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Recorded tool stdout verdict

RESULT: prints unsupported

Recorded in `measure/rounds/r0001/overhang-white_bishop.log` (sha256 dee9e1c436756ed2e2701f2bae22594d196b857ce1a9a6320b10497774b02088). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
