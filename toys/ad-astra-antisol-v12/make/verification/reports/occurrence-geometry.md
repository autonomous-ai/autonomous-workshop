# Occurrence geometry, this run against the published set

`antisol.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 200 labels carry 220 solids.

- labels published: 200, carrying 220 solids
- labels in this run: 200, carrying 220 solids
- identical in geometry: 181

## Gone

None.

## New

None.

## Changed geometry

- `corona_e9_cyan` — volume 20488.066304 -> 19754.771123 mm3
- `mercury_anti_caloris_floor_white` — bounding box moved by 1.35e-01 mm
- `mercury_anti_caloris_rim_cocoa_brown` — bounding box moved by 1.59e-01 mm
- `mercury_anti_globe_gray` — bounding box moved by 1.26e-01 mm
- `mercury_anti_plains1_cocoa_brown` — bounding box moved by 8.57e+00 mm
- `mercury_anti_plains2_cocoa_brown` — bounding box moved by 1.14e+00 mm
- `mercury_anti_plains3_cocoa_brown` — bounding box moved by 7.57e+00 mm
- `mercury_anti_plains4_cocoa_brown` — bounding box moved by 8.97e+00 mm
- `venus_anti_globe_sunflower_yellow` — volume 2163.854548 -> 2162.408911 mm3
- `venus_anti_highland1_beige` — bounding box moved by 2.71e+00 mm
- `venus_anti_highland2_beige` — bounding box moved by 5.60e+00 mm
- `venus_anti_highland3_beige` — bounding box moved by 8.95e+00 mm
- `venus_anti_highland4_beige` — bounding box moved by 7.67e+00 mm
- `venus_anti_highland5_beige` — bounding box moved by 7.28e+00 mm
- `venus_anti_highland6_beige` — volume 2.472607 -> 3.208736 mm3
- `venus_anti_highland7_beige` — volume 1.163490 -> 2.472607 mm3
- `venus_anti_lowland1_cocoa_brown` — bounding box moved by 5.96e-01 mm
- `venus_anti_lowland2_cocoa_brown` — volume 20.403365 -> 19.803756 mm3
- `venus_anti_lowland3_cocoa_brown` — bounding box moved by 5.24e+00 mm

## Verdict

Nothing outside `mercury_anti_*` and `venus_anti_*` and `corona_*` gained, lost or moved a solid.
