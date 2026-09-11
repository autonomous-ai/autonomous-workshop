# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_05.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_05.md`

part_fork_05.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_fork_05.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     22.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_05.md
```

Printed STEP SHA-256: `4ff666793a0bbc5a0cd8158425dca45e60a4d0932c88f13df7ba6e49d21d78aa`. Captured log SHA-256: `192860eb594fc2094253637ae97f62c301c9d26be2ad46fba21e815442ec34e7`.
