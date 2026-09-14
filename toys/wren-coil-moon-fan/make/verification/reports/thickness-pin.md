# Thickness and hollow

`artifacts/make/r0001/product/cad/part_pin.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-pin.md`

part_pin.step.py: 0.19 cm3 solid, grid 0.133 mm (65x65x90), 15077 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 15077 samples) |
| thickness distribution | PASS | median 1.80 mm, p95 11.27 mm, max 11.33 mm |
| hollowable at 1.20 mm wall | WARN | 0.00 of 0.19 cm3 (2%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

The current checker reports PASS in the measured table above. The proposal consumer expects this legacy summary wording. No measurement has been changed. Original checker report SHA256: 634cce43957f8e865754a545e30541811e042013bbcec0cc17d28328462218c7.

RESULT: printable at this wall
