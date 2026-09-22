# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-sun.md`

part_sun.step.py: 659.4 cm2 of surface, grid 0.463 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_sun.step.py: 659.4 cm2 of surface, grid 0.463 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     39.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-sun.md
```

Printed STEP SHA-256: `434fa1bddf8275074682f6cf914c4908b9e94ff8be361fb5b276e779be9286da`. Captured log SHA-256: `d0512432d43297d9c18229091a6bf3266322defed2f3862e255e561cf1381d0d`.
