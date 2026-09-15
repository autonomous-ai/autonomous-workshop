# Overhang and support

`artifacts/make/r0001/product/cad/part_black_rook.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-black_rook.md`

part_black_rook.step.py: 9.1 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 13.9% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Report-format compatibility summary

RESULT: prints unsupported

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: 1fb68de028ceeb351ce7895c6d5c8bf780ef4a4fb4f75d12b8d97a0486e07009.
