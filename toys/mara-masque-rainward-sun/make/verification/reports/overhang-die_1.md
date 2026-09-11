# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_die_1.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-die_1.md`

part_die_1.step.py: 15.4 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.7% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_die_1.step.py: 15.4 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     16.7% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-die_1.md
```

Printed STEP SHA-256: `f05d89270dffd84c9db19b85dbf32a2dbcd1174dcc6dcf35e1937d426a57dbea`. Captured log SHA-256: `ce5fa924ca8bda4e24d1c9f9ec9b122d93d3dc4cac98a0762059b7bc0fb34ea5`.
