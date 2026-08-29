# Thickness and hollow

> Archived display-layout mesh measurement. `night_sky_weave.stl` is not a print target; strict printable-part verification applies to the three family STL reports.

`artifacts/make/r0001/product/cad/night_sky_weave.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-night_sky_weave.md`

artifacts/make/r0001/product/cad/night_sky_weave.stl: 46.81 cm3 solid, grid 0.179 mm (556x556x36), 382763 surface samples, thickness resolved to 0.089 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 382763 samples) |
| thickness distribution | PASS | median 5.54 mm, p95 31.45 mm, max 41.27 mm |
| hollowable at 1.20 mm wall | WARN | 18.54 of 46.81 cm3 (40%) in 9 pocket(s) |
| filament that would save | PASS | 2.78 cm3, 3.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
