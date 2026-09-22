# Occurrence geometry, this run against the published set

`antisol.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 216 labels carry 236 solids.

- labels published: 216, carrying 236 solids
- labels in this run: 204, carrying 224 solids
- identical in geometry: 196

## Gone

- `neptune_anti_streaks1_white`
- `neptune_anti_streaks2_white`
- `neptune_anti_streaks3_white`
- `neptune_anti_streaks4_white`
- `neptune_anti_streaks5_white`
- `neptune_anti_streaks6_white`
- `neptune_anti_streaks7_white`
- `neptune_anti_streaks8_white`
- `neptune_anti_streaks9_white`
- `neptune_sol_streaks1_white`
- `neptune_sol_streaks2_white`
- `neptune_sol_streaks3_white`
- `neptune_sol_streaks4_white`
- `neptune_sol_streaks5_white`
- `neptune_sol_streaks6_white`
- `neptune_sol_streaks7_white`
- `neptune_sol_streaks8_white`
- `neptune_sol_streaks9_white`

## New

- `neptune_anti_bands1_white`
- `neptune_anti_bands2_white`
- `neptune_anti_bands3_white`
- `neptune_sol_bands1_white`
- `neptune_sol_bands2_white`
- `neptune_sol_bands3_white`

## Changed geometry

- `neptune_anti_globe_blue` — volume 5315.691954 -> 5419.597585 mm3
- `neptune_sol_globe_blue` — volume 5328.672017 -> 5419.597517 mm3

## Verdict

Nothing outside `neptune_sol_*` and `neptune_anti_*` gained, lost or moved a solid.
