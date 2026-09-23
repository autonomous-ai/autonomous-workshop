# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_coupon.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0004/overhang-coupon.md`

part_coupon.step.py: 23.1 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 35.8% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
