# Occurrence geometry, this run against the published set

`antisol.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 200 labels carry 220 solids.

- labels published: 200, carrying 220 solids
- labels in this run: 200, carrying 220 solids
- identical in geometry: 193

## Gone

None.

## New

None.

## Changed geometry

- `jupiter_anti_bands1_cocoa_brown` — bounding box moved by 4.45e-01 mm
- `jupiter_anti_bands2_cocoa_brown` — bounding box moved by 3.72e-01 mm
- `jupiter_anti_collar_cocoa_brown` — bounding box moved by 5.04e+00 mm
- `jupiter_anti_spot_red` — bounding box moved by 4.96e+00 mm
- `jupiter_anti_zones1_beige` — bounding box moved by 2.32e-01 mm
- `jupiter_anti_zones2_beige` — bounding box moved by 4.66e-01 mm
- `jupiter_anti_zones3_beige` — bounding box moved by 4.14e-01 mm

## Verdict

Nothing outside `jupiter_anti_*` gained, lost or moved a solid.
