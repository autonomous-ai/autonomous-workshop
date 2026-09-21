# Overhang and support

`artifacts/make/r0001/product/cad/part_single_06.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-single_06.md`

part_single_06.step.py: 2.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.2% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured console verdict

The matching current-run check printed the following result. Its measured report content is identical to this final report; only command paths differ. Source: `rounds/r0001/overhang-single_06.log` (SHA256 `31d1eb725123e1402123d06a424a112fe29b026dc82ab18933b889a7f6c0d27a`).

RESULT: prints unsupported
