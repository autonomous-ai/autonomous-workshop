# Thickness and hollow

`artifacts/make/r0001/product/cad/part_face_sleepy.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-face_sleepy.md`

part_face_sleepy.step.py: 1.26 cm3 solid, grid 0.133 mm (155x220x30), 74340 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 74340 samples) |
| thickness distribution | PASS | median 2.40 mm, p95 23.93 mm, max 31.40 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.26 cm3 (0%) in 0 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Workshop report-format compatibility summary

RESULT: printable at this wall

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 0fc4f80edf7f36aa1fe6d0d82d11034c2c823360d3489b5b4bb96288e43fdfd2.
