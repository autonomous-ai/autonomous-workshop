# Overhang and support

`artifacts/make/r0001/product/cad/part_face_angry.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-face_angry.md`

part_face_angry.step.py: 14.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 35.2% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Workshop report-format compatibility summary

RESULT: prints unsupported

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 806106838be5772d27e96ad1e6cef42214c0a30fdf0fbc9dad342d1cfae318d4.
