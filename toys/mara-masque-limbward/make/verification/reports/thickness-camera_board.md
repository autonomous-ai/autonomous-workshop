# Thickness and hollow

`artifacts/make/r0001/product/cad/part_camera_board.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-camera_board.md`

part_camera_board.step.py: 825.65 cm3 solid, grid 0.452 mm (439x439x62), 359484 surface samples, thickness resolved to 0.226 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.23) | PASS | 0.0% of surface below (0 of 359484 samples); 27 more within measurement error of the limit |
| thickness distribution | PASS | median 22.12 mm, p95 195.96 mm, max 271.59 mm |
| hollowable at 1.20 mm wall | WARN | 698.84 of 825.65 cm3 (85%) in 1 pocket(s) |
| filament that would save | PASS | 104.83 cm3, 130.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0002/thickness-camera_board.log` (sha256 8258907597a6ce745cca642f937c3cf3fa536bdd1ac06a3bf3a61ff5deba66b5). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
