# Overhang and support

`artifacts/make/r0001/product/cad-project/part_locomotive_axle_keeper.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-locomotive_axle_keeper.md`

artifacts/make/r0001/product/cad-project/part_locomotive_axle_keeper.stl: 15.1 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.2% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
