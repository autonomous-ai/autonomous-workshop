# Overhang and support

`artifacts/make/r0001/product/cad/part_roller_left.stl --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-roller_left.md`

artifacts/make/r0001/product/cad/part_roller_left.stl: 4.0 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
