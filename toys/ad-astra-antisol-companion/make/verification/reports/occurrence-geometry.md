# Occurrence geometry, this run against the published set

`assembled.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 200 labels carry 220 solids.

- labels published: 200, carrying 220 solids
- labels in this run: 202, carrying 222 solids
- identical in geometry: 178

## Gone

None.

## New

- `neptune_anti_companion_white`
- `neptune_sol_companion_white`

## Every label whose measurement differs

- `earth_anti_numeral1_white` — bounding box moved by 3.29e+01 mm
- `earth_anti_numeral2_white` — bounding box moved by 3.29e+01 mm
- `jupiter_anti_numeral1_white` — bounding box moved by 3.29e+01 mm
- `jupiter_anti_numeral2_white` — bounding box moved by 3.29e+01 mm
- `mars_sol_numeral1_black` — bounding box moved by 3.28e+01 mm
- `mars_sol_numeral2_black` — bounding box moved by 3.28e+01 mm
- `mercury_anti_numeral1_white` — bounding box moved by 3.27e+01 mm
- `mercury_anti_numeral2_white` — bounding box moved by 3.27e+01 mm
- `mercury_anti_numeral3_white` — bounding box moved by 3.31e+01 mm
- `mercury_anti_numeral4_white` — bounding box moved by 3.31e+01 mm
- `mercury_sol_numeral3_black` — bounding box moved by 3.30e+01 mm
- `mercury_sol_numeral4_black` — bounding box moved by 3.30e+01 mm
- `neptune_anti_globe_blue` — volume 5419.597585 -> 5419.512230 mm3
- `neptune_anti_spot_dark_gray` — volume 11.931873 -> 10.511314 mm3
- `neptune_sol_globe_blue` — volume 5419.597517 -> 5419.512165 mm3
- `neptune_sol_spot_dark_gray` — volume 11.931873 -> 10.511314 mm3
- `saturn_anti_numeral3_white` — bounding box moved by 3.31e+01 mm
- `saturn_anti_numeral4_white` — bounding box moved by 3.31e+01 mm
- `uranus_anti_numeral1_white` — bounding box moved by 3.29e+01 mm
- `uranus_anti_numeral2_white` — bounding box moved by 3.29e+01 mm
- `venus_sol_numeral1_black` — bounding box moved by 3.28e+01 mm
- `venus_sol_numeral2_black` — bounding box moved by 3.28e+01 mm

## Relabelled rather than moved

`assemblies/product.place()` numbers the separate solids of one
colour region `<stem>1`, `<stem>2` and so on, in whatever order
the kernel hands them back, and that order is not stable between
runs. Where a whole numbered family comes back carrying exactly
the same set of solids under a different assignment of numbers,
that is the numbering and not the geometry, and it is separated
out here rather than counted as a change. The test is on the
MULTISET: every (solid count, volume, bounding box) in the family
must appear the same number of times in both runs.

- `earth_anti_numeral_white*` — `earth_anti_numeral1_white`, `earth_anti_numeral2_white`: same 2 solids, numbers permuted
- `jupiter_anti_numeral_white*` — `jupiter_anti_numeral1_white`, `jupiter_anti_numeral2_white`: same 2 solids, numbers permuted
- `mars_sol_numeral_black*` — `mars_sol_numeral1_black`, `mars_sol_numeral2_black`: same 2 solids, numbers permuted
- `mercury_anti_numeral_white*` — `mercury_anti_numeral1_white`, `mercury_anti_numeral2_white`, `mercury_anti_numeral3_white`, `mercury_anti_numeral4_white`: same 4 solids, numbers permuted
- `mercury_sol_numeral_black*` — `mercury_sol_numeral1_black`, `mercury_sol_numeral2_black`, `mercury_sol_numeral3_black`, `mercury_sol_numeral4_black`: same 4 solids, numbers permuted
- `saturn_anti_numeral_white*` — `saturn_anti_numeral1_white`, `saturn_anti_numeral2_white`, `saturn_anti_numeral3_white`, `saturn_anti_numeral4_white`: same 4 solids, numbers permuted
- `uranus_anti_numeral_white*` — `uranus_anti_numeral1_white`, `uranus_anti_numeral2_white`: same 2 solids, numbers permuted
- `venus_sol_numeral_black*` — `venus_sol_numeral1_black`, `venus_sol_numeral2_black`: same 2 solids, numbers permuted

## Changed geometry, after that

- `neptune_anti_globe_blue` — volume 5419.597585 -> 5419.512230 mm3
- `neptune_anti_spot_dark_gray` — volume 11.931873 -> 10.511314 mm3
- `neptune_sol_globe_blue` — volume 5419.597517 -> 5419.512165 mm3
- `neptune_sol_spot_dark_gray` — volume 11.931873 -> 10.511314 mm3

## Verdict

Nothing outside `neptune_sol_*` and `neptune_anti_*` gained, lost or moved a solid.
