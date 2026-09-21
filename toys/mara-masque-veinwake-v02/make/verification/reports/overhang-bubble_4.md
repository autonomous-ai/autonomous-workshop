# Overhang and support

`cad/veinwake/part_bubble_4.step.py --angle 45.0 --report cad/veinwake/measure/overhang-bubble_4.md`

part_bubble_4.step.py: 30.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.1% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/overhang-bubble_4.md`, SHA-256 `ec5d4886ee86fd4b76c212579d8b2a56452cca153a8aac72a07a00c7ff4a7f22`.

RESULT: prints unsupported
