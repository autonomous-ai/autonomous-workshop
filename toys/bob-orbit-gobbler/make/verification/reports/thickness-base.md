# Thickness and hollow

`cad/part_base.stl --nozzle 0.4 --report cad/measure/thickness-base.md`

cad/part_base.stl: 130.12 cm3 solid, grid 0.239 mm (798x297x47), 399026 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 399026 samples) |
| thickness distribution | PASS | median 10.06 mm, p95 69.92 mm, max 189.88 mm |
| hollowable at 1.20 mm wall | WARN | 91.85 of 130.12 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 13.78 cm3, 17.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
