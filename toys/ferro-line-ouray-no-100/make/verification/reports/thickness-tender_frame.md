# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_frame.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_frame.md`

artifacts/make/r0001/product/cad-project/part_tender_frame.stl: 6.42 cm3 solid, grid 0.133 mm (417x185x42), 191328 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 191328 samples) |
| thickness distribution | PASS | median 4.93 mm, p95 54.93 mm, max 54.93 mm |
| hollowable at 1.20 mm wall | WARN | 2.74 of 6.42 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.41 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
