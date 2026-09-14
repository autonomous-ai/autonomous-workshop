# Overhang and support

`artifacts/make/r0001/product/cad/part_leaf.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-leaf.md`

part_leaf.step.py: 61.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 43.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Report-format compatibility summary

The current checker reports PASS in the measured table above. The proposal consumer expects this legacy summary wording. No measurement has been changed. Original checker report SHA256: f9de03c706822e298ebb239f39454c7bccafddb08f5d4daa59e3ae850e9892ae.

RESULT: prints unsupported
