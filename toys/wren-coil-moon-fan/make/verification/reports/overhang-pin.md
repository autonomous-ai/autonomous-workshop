# Overhang and support

`artifacts/make/r0001/product/cad/part_pin.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-pin.md`

part_pin.step.py: 3.0 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Report-format compatibility summary

The current checker reports PASS in the measured table above. The proposal consumer expects this legacy summary wording. No measurement has been changed. Original checker report SHA256: 83396ba196a344b698f6703b09ce765fe35453d4569126afa09881581f0a1e69.

RESULT: prints unsupported
