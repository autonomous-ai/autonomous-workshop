# Overhang and support

`artifacts/make/r0001/product/cad/part_base.step.py --angle 45 --report artifacts/make/r0001/product/cad/measure/overhang-base.md`

part_base.step.py: 919.5 cm2 of surface, grid 0.441 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.3% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Tool terminal verdict

The following line is preserved verbatim from this same invocation’s stdout:

```text
RESULT: prints unsupported
```
