# Occurrence geometry, this run against the published set

`antisol.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 212 labels carry 232 solids.

- labels published: 212, carrying 232 solids
- labels in this run: 216, carrying 236 solids
- identical in geometry: 208

## Gone

- `uranus_anti_band_white`
- `uranus_sol_band_white`

## New

- `uranus_anti_hood_north_beige`
- `uranus_anti_hood_south_beige`
- `uranus_anti_ring_cyan`
- `uranus_sol_hood_north_beige`
- `uranus_sol_hood_south_beige`
- `uranus_sol_ring_cyan`

## Changed geometry

- `uranus_anti_globe_cyan` — volume 5379.797282 -> 5323.412371 mm3
- `uranus_sol_globe_cyan` — volume 5379.797397 -> 5323.412384 mm3

## Verdict

Nothing outside `uranus_sol_*` and `uranus_anti_*` gained, lost or moved a solid.
