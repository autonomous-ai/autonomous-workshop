# Occurrence geometry, this run against the published set

`antisol.step` -> `assembled.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 200 labels carry 220 solids.

- labels published: 200, carrying 220 solids
- labels in this run: 212, carrying 232 solids
- identical in geometry: 190

## Gone

None.

## New

- `neptune_anti_streaks4_white`
- `neptune_anti_streaks5_white`
- `neptune_anti_streaks6_white`
- `neptune_anti_streaks7_white`
- `neptune_anti_streaks8_white`
- `neptune_anti_streaks9_white`
- `neptune_sol_streaks4_white`
- `neptune_sol_streaks5_white`
- `neptune_sol_streaks6_white`
- `neptune_sol_streaks7_white`
- `neptune_sol_streaks8_white`
- `neptune_sol_streaks9_white`

## Changed geometry

- `neptune_anti_globe_blue` — volume 5421.296930 -> 5315.691954 mm3
- `neptune_anti_spot_dark_gray` — volume 10.232521 -> 11.931873 mm3
- `neptune_anti_streaks1_white` — volume 4.707744 -> 16.131575 mm3
- `neptune_anti_streaks2_white` — volume 4.462534 -> 16.013414 mm3
- `neptune_anti_streaks3_white` — volume 1.634069 -> 15.367410 mm3
- `neptune_sol_globe_blue` — volume 5421.573443 -> 5328.672017 mm3
- `neptune_sol_spot_dark_gray` — volume 9.955944 -> 11.931873 mm3
- `neptune_sol_streaks1_white` — volume 4.707744 -> 16.131575 mm3
- `neptune_sol_streaks2_white` — volume 4.462534 -> 15.452402 mm3
- `neptune_sol_streaks3_white` — volume 1.634069 -> 15.367410 mm3

## Verdict

Nothing outside `neptune_sol_*` and `neptune_anti_*` gained, lost or moved a solid.
